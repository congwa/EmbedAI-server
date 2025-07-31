from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.sql import func
from fastapi import HTTPException, status
from app.models.chat import Chat, ChatMessage, MessageType
from app.models.third_party_user import ThirdPartyUser
from app.models.user import User
from app.models.enums import ChatMode
from app.services.knowledge_base import KnowledgeBaseService
from app.core.logger import Logger
from app.core.redis_manager import redis_manager
from app.core.ws import connection_manager

class ChatService:
    """聊天服务类
    
    处理第三方用户与知识库的聊天相关业务逻辑
    包括创建会话、发送消息、获取历史记录等
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.kb_service = KnowledgeBaseService(db)

    async def _cache_chat(self, chat: Chat) -> None:
        """缓存聊天会话信息到Redis"""
        await redis_manager.cache_chat(
            chat_id=chat.id,
            chat_data={
                "id": chat.id,
                "title": chat.title or "",
                "chat_mode": chat.chat_mode,
                "is_active": chat.is_active,
                "third_party_user_id": chat.third_party_user_id,
                "knowledge_base_id": chat.knowledge_base_id,
                "current_admin_id": chat.current_admin_id or 0,
                "last_message_at": chat.last_message_at.strftime("%Y-%m-%d %H:%M:%S") if chat.last_message_at else None,
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )
        
    async def _get_cached_chat(self, chat_id: int) -> Optional[Dict]:
        """从Redis获取缓存的聊天会话信息"""
        return await redis_manager.get_cached_chat(chat_id)
        
    async def _cache_message(self, message: ChatMessage) -> None:
        """缓存消息到Redis"""
        await redis_manager.cache_message(
            chat_id=message.chat_id,
            message_data={
                "id": message.id,
                "content": message.content,
                "message_type": message.message_type,
                "created_at": message.created_at,
                "is_read": message.is_read,
                "sender_id": message.sender_id or 0,
                "doc_metadata": message.doc_metadata or {}
            }
        )
        
    async def _get_cached_messages(
        self,
        chat_id: int,
        start: int = 0,
        end: int = -1
    ) -> List[Dict]:
        """从Redis获取缓存的消息"""
        return await redis_manager.get_cached_messages(chat_id, start, end)
        
    async def get_or_create_third_party_user(self, third_party_user_id: int) -> ThirdPartyUser:
        """获取或创建第三方用户
        
        Args:
            third_party_user_id: 第三方用户ID
            
        Returns:
            ThirdPartyUser: 第三方用户对象
        """
        user = (await self.db.execute(
            select(ThirdPartyUser).filter(ThirdPartyUser.id == third_party_user_id)
        )).scalar_one_or_none()
        
        if not user:
            user = ThirdPartyUser(id=third_party_user_id)
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            Logger.info(f"Created new third party user with ID {third_party_user_id}")
            
        return user

    async def create_chat(
        self,
        third_party_user_id: int,
        kb_id: int,
        title: Optional[str] = None
    ) -> Chat:
        """创建新的聊天会话
        
        Args:
            third_party_user_id: 第三方用户ID
            kb_id: 知识库ID
            title: 会话标题（可选）
            
        Returns:
            Chat: 创建的会话对象
            
        Raises:
            HTTPException: 当知识库不存在时
        """
        user = await self.get_or_create_third_party_user(third_party_user_id)
            
        chat = Chat(
            third_party_user_id=third_party_user_id,
            knowledge_base_id=kb_id,
            title=title,
            messages=[]  # 初始化为空列表
        )
        
        Logger.info(f"Creating chat with third_party_user_id: {third_party_user_id}, kb_id: {kb_id}, title: {title}")
        
        try:
            self.db.add(chat)
            await self.db.commit()
            await self.db.refresh(chat)
        except Exception as e:
            Logger.error(f"Error creating chat: {str(e)}")
            raise HTTPException(status_code=500, detail="Error creating chat")
        
        await self._cache_chat(chat)

        return chat

    async def get_chat(self, chat_id: int) -> Chat:
        """获取聊天会话
        
        首先尝试从Redis缓存获取，如果没有则从数据库获取并缓存
        """
        # 尝试从缓存获取
        cached = await self._get_cached_chat(chat_id)
        if cached:
            chat = Chat()
            for key, value in cached.items():
                if key == "last_message_at":
                    value = datetime.fromtimestamp(value)
                elif key == "updated_at":
                    value = datetime.fromtimestamp(value)
                setattr(chat, key, value)
            return chat
            
        # 从数据库获取
        chat = await self.db.execute(
            select(Chat).filter(Chat.id == chat_id)
        )
        chat = chat.scalar_one_or_none()
        
        if not chat:
            Logger.warning(f"Chat {chat_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="聊天会话不存在"
            )
            
        # 缓存到Redis
        await self._cache_chat(chat)
        return chat

    async def get_chat_info(
        self,
        chat_id: int
    ) -> Dict[str, int]:
        """获取聊天会话的基本信息
        
        Args:
            chat_id: 会话ID
            
        Returns:
            Dict[str, int]: 包含知识库ID和用户ID的字典
            
        Raises:
            HTTPException: 当会话不存在时
        """
        # 尝试从缓存获取
        cached = await self._get_cached_chat(chat_id)
        if cached:
            return {
                "knowledge_base_id": cached["knowledge_base_id"],
                "third_party_user_id": cached["third_party_user_id"]
            }
            
        # 从数据库获取
        result = (await self.db.execute(
            select(Chat.knowledge_base_id, Chat.third_party_user_id)
            .filter(Chat.id == chat_id)
        )).first()
        
        if not result:
            Logger.warning(f"Chat {chat_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="聊天会话不存在"
            )
            
        kb_id, user_id = result
        Logger.debug(f"Retrieved chat info: chat_id={chat_id}, kb_id={kb_id}, user_id={user_id}")
        
        return {
            "knowledge_base_id": kb_id,
            "third_party_user_id": user_id
        }

    async def check_chat_ownership(
        self,
        chat_id: int,
        third_party_user_id: int
    ) -> bool:
        """检查聊天会话是否属于指定用户
        
        Args:
            chat_id: 会话ID
            third_party_user_id: 第三方用户ID
            
        Returns:
            bool: 是否属于该用户
        """
        # 尝试从缓存获取
        cached = await self._get_cached_chat(chat_id)
        if cached:
            return cached["third_party_user_id"] == third_party_user_id
            
        # 从数据库获取
        result = (await self.db.execute(
            select(Chat.id)
            .filter(
                and_(
                    Chat.id == chat_id,
                    Chat.third_party_user_id == third_party_user_id
                )
            )
        )).first()
        
        is_owner = result is not None
        Logger.debug(f"Chat ownership check: chat_id={chat_id}, user_id={third_party_user_id}, is_owner={is_owner}")
        return is_owner

    async def list_user_chats(
        self,
        third_party_user_id: int,
        kb_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 20,
        include_deleted: bool = False
    ) -> List[Chat]:
        """获取用户的聊天会话列表
        
        Args:
            third_party_user_id: 第三方用户ID
            kb_id: 知识库ID（可选，用于筛选特定知识库的会话）
            skip: 分页起始位置
            limit: 每页数量
            include_deleted: 是否包含已删除的会话
            
        Returns:
            List[Chat]: 会话列表
        """
        # 确保用户存在
        await self.get_or_create_third_party_user(third_party_user_id)
        
        query = select(Chat).filter(Chat.third_party_user_id == third_party_user_id)
        
        if kb_id is not None:
            query = query.filter(Chat.knowledge_base_id == kb_id)
            
        if not include_deleted:
            query = query.filter(Chat.is_deleted == False)
            
        query = query.order_by(Chat.updated_at.desc()).offset(skip).limit(limit)
        
        chats = (await self.db.execute(query)).scalars().all()
        
        # 缓存会话信息
        for chat in chats:
            await self._cache_chat(chat)
            
        Logger.debug(f"Retrieved {len(chats)} chats for third party user {third_party_user_id}")
        return chats

    async def add_message(
        self,
        chat_id: int,
        content: str,
        message_type: MessageType,
        sender_id: Optional[int] = None,
        doc_metadata: Optional[dict] = None
    ) -> ChatMessage:
        """添加新消息"""
        chat = await self.get_chat(chat_id)
        
        message = ChatMessage(
            chat_id=chat_id,
            content=content,
            message_type=message_type,
            sender_id=sender_id,
            doc_metadata=doc_metadata
        )
        self.db.add(message)
        
        # 更新会话的最后消息时间
        chat.last_message_at = datetime.now()
        
        await self.db.commit()
        await self.db.refresh(message)
        
        # 缓存消息
        await self._cache_message(message)
        # 更新会话缓存
        await self._cache_chat(chat)
        
        # 广播消息
        await connection_manager.broadcast_to_chat(
            chat_id,
            {
                "type": "message",
                "data": {
                    "id": message.id,
                    "content": message.content,
                    "message_type": message.message_type,
                    "created_at": message.created_at,
                    "sender_id": message.sender_id,
                    "doc_metadata": message.doc_metadata
                }
            }
        )
        
        return message

    async def get_chat_messages(
        self,
        chat_id: int,
        user_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> List[ChatMessage]:
        """获取聊天消息历史
        
        Args:
            chat_id: 会话ID
            user_id: 第三方用户ID
            skip: 分页起始位置
            limit: 每页数量
            
        Returns:
            List[ChatMessage]: 消息列表
            
        Raises:
            HTTPException: 当会话不存在或用户无权访问时
        """
        # 验证用户是否有权限访问该会话
        await self.get_chat(chat_id)
        
        messages = (await self.db.execute(
            select(ChatMessage)
            .filter(ChatMessage.chat_id == chat_id)
            .order_by(ChatMessage.created_at)
            .offset(skip)
            .limit(limit)
        )).scalars().all()
        
        Logger.debug(f"Retrieved {len(messages)} messages from chat {chat_id}")
        return messages

    async def delete_chat(
        self,
        chat_id: int,
        user_id: int
    ) -> None:
        """软删除聊天会话
        
        Args:
            chat_id: 会话ID
            user_id: 第三方用户ID
            
        Raises:
            HTTPException: 当会话不存在或用户无权访问时
        """
        chat = await self.get_chat(chat_id)
        
        # 软删除
        chat.is_deleted = True
        chat.deleted_at = datetime.now()
        await self.db.commit()
        
        Logger.info(f"Soft deleted chat {chat_id}")

    async def resume_chat(
        self,
        chat_id: int,
        user_id: int
    ) -> Chat:
        """恢复聊天会话
        
        Args:
            chat_id: 会话ID
            user_id: 第三方用户ID
            
        Returns:
            Chat: 会话对象，包含所有消息历史
            
        Raises:
            HTTPException: 当会话不存在或用户无权访问时
        """
        # 检查会话是否存在且属于该用户
        chat = await self.get_chat(chat_id)
        
        # 预加载所有消息
        await self.db.refresh(chat, ['messages'])
        
        Logger.info(f"Resumed chat {chat_id} for user {user_id} with {len(chat.messages)} messages")
        return chat

    async def get_chat_context(
        self,
        chat_id: int,
        limit: int = 10
    ) -> List[ChatMessage]:
        """获取聊天上下文
        
        Args:
            chat_id: 会话ID
            limit: 返回最近的消息数量
            
        Returns:
            List[ChatMessage]: 最近的消息列表
        """
        messages = (await self.db.execute(
            select(ChatMessage)
            .filter(ChatMessage.chat_id == chat_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )).scalars().all()
        
        # 反转消息列表，使其按时间正序排列
        messages.reverse()
        
        Logger.debug(f"Retrieved {len(messages)} context messages for chat {chat_id}")
        return messages

    async def get_message_history(
        self,
        chat_id: int,
        before_message_id: Optional[int] = None,
        limit: int = 20
    ) -> List[ChatMessage]:
        """获取聊天历史记录
        
        Args:
            chat_id: 会话ID
            before_message_id: 在此消息ID之前的消息 (用于分页)
            limit: 返回的消息数量
            
        Returns:
            List[ChatMessage]: 消息列表 (按时间正序)
        """
        query = (
            select(ChatMessage)
            .filter(ChatMessage.chat_id == chat_id)
        )
        
        if before_message_id:
            query = query.filter(ChatMessage.id < before_message_id)
            
        # Fetch the most recent messages in the selected range
        query = query.order_by(ChatMessage.created_at.desc()).limit(limit)
        
        messages = (await self.db.execute(query)).scalars().all()
        
        # Reverse the list to return messages in chronological order
        messages.reverse()
        
        Logger.debug(f"Retrieved {len(messages)} history messages for chat {chat_id} before message {before_message_id}")
        return messages

    async def restore_chat(
        self,
        chat_id: int,
        admin_user_id: int
    ) -> Chat:
        """恢复已删除的聊天会话
        
        Args:
            chat_id: 会话ID
            admin_user_id: 管理员用户ID
            
        Returns:
            Chat: 恢复的会话对象
            
        Raises:
            HTTPException: 当会话不存在或已经是活跃状态时
        """
        # 查找会话，包括已删除的
        chat = (await self.db.execute(
            select(Chat)
            .filter(Chat.id == chat_id)
            .filter(Chat.is_deleted == True)  # 只恢复已删除的会话
            .options(selectinload(Chat.messages))
        )).scalar_one_or_none()
        
        if not chat:
            Logger.warning(f"Chat {chat_id} not found or not deleted")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="聊天会话不存在或未被删除"
            )
            
        # 恢复会话
        chat.is_deleted = False
        chat.deleted_at = None
        await self.db.commit()
        await self.db.refresh(chat)
        
        Logger.info(f"Restored chat {chat_id} by admin {admin_user_id}")
        return chat

    async def list_admin_chats(
        self,
        admin_id: int,
        skip: int = 0,
        limit: int = 20,
        include_inactive: bool = False
    ) -> List[Chat]:
        """获取管理员可见的聊天会话列表"""
        query = select(Chat).filter(
            or_(
                Chat.current_admin_id == admin_id,
                and_(
                    Chat.chat_mode == ChatMode.AI,
                    Chat.is_deleted == False
                )
            )
        )
        
        if not include_inactive:
            query = query.filter(Chat.is_active == True)
            
        query = query.order_by(Chat.last_message_at.desc())
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def switch_chat_mode(
        self,
        chat_id: int,
        admin_id: int,
        mode: ChatMode
    ) -> Chat:
        """切换聊天模式"""
        chat = await self.get_chat(chat_id)
        
        # 检查管理员权限
        admin = await self.db.execute(
            select(User).filter(User.id == admin_id)
        )
        admin = admin.scalar_one_or_none()
        if not admin or not admin.is_admin:
            raise HTTPException(status_code=403, detail="Only admin can switch chat mode")
        
        if mode == ChatMode.HUMAN:
            # 切换到人工模式
            chat.chat_mode = ChatMode.HUMAN
            chat.current_admin_id = admin_id
            
            # 添加系统消息
            await self.add_system_message(
                chat_id=chat_id,
                content="已切换到人工服务模式"
            )
        else:
            # 切换回AI模式
            chat.chat_mode = ChatMode.AI
            chat.current_admin_id = None
            
            await self.add_system_message(
                chat_id=chat_id,
                content="已切换到AI助手模式"
            )
        
        await self.db.commit()
        return chat

    async def add_system_message(
        self,
        chat_id: int,
        content: str
    ) -> ChatMessage:
        """添加系统消息"""
        return await self.add_message(
            chat_id=chat_id,
            content=content,
            message_type=MessageType.SYSTEM
        )

    async def mark_messages_as_read(
        self,
        chat_id: int,
        user_id: int
    ) -> None:
        """将消息标记为已读"""
        messages = await self.db.execute(
            select(ChatMessage).filter(
                ChatMessage.chat_id == chat_id,
                ChatMessage.is_read == False,
                ChatMessage.sender_id != user_id
            )
        )
        
        for message in messages.scalars():
            message.is_read = True
        
        await self.db.commit()
    
    async def get_unread_count(
        self,
        chat_id: int,
        user_id: int
    ) -> int:
        """获取未读消息数量"""
        result = await self.db.execute(
            select(ChatMessage).filter(
                ChatMessage.chat_id == chat_id,
                ChatMessage.is_read == False,
                ChatMessage.sender_id != user_id
            )
        )
        return len(result.scalars().all())

    async def list_messages(
        self,
        chat_id: int,
        page: int = 1,
        page_size: int = 50,
        use_cache: bool = True
    ) -> Tuple[List[ChatMessage], int]:
        """获取消息列表，支持分页
        
        Args:
            chat_id: 会话ID
            page: 页码（从1开始）
            page_size: 每页大小
            use_cache: 是否使用缓存
            
        Returns:
            Tuple[List[ChatMessage], int]: (消息列表, 总数)
        """
        if use_cache:
            # 计算缓存的起始和结束位置
            start = (page - 1) * page_size
            end = start + page_size - 1
            
            cached_messages = await self._get_cached_messages(chat_id, start, end)
            if cached_messages:
                # 将缓存的消息转换为ChatMessage对象
                messages = []
                for msg_data in cached_messages:
                    message = ChatMessage()
                    for key, value in msg_data.items():
                        if key == "is_read":
                            value = bool(value)
                        elif key == "created_at":
                            value = datetime.fromtimestamp(value)
                        setattr(message, key, value)
                    messages.append(message)
                return messages, len(cached_messages)
                
        # 从数据库获取
        query = select(ChatMessage).filter(
            ChatMessage.chat_id == chat_id
        ).order_by(desc(ChatMessage.created_at))
        
        # 获取总数
        total = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = total.scalar_one()
        
        # 分页查询
        messages = await self.db.execute(
            query.offset((page - 1) * page_size).limit(page_size)
        )
        messages = messages.scalars().all()
        
        # 缓存消息
        for message in messages:
            await self._cache_message(message)
            
        return messages, total