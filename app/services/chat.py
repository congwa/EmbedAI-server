from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.orm import Session, selectinload
from fastapi import HTTPException, status
from app.models.chat import Chat, ChatMessage, MessageType, message_read_status
from app.models.identity import UserIdentity
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
        """缓存消息到Redis - (已禁用，待重构)"""
        # TODO: 重构以支持新的 `read_by` 结构
        pass

    async def _get_cached_messages(
            self,
            chat_id: int,
            start: int = 0,
            end: int = -1
    ) -> List[Dict]:
        """从Redis获取缓存的消息 - (已禁用，待重构)"""
        # TODO: 重构以支持新的 `read_by` 结构
        return []

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
        cached_chat_data = await self._get_cached_chat(chat_id)
        if cached_chat_data:
            # Manually construct a Chat object from cached data
            chat = Chat(**cached_chat_data)
            return chat

        # 从数据库获取
        chat = (await self.db.execute(
            select(Chat).filter(Chat.id == chat_id)
        )).scalar_one_or_none()

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
        """获取用户的聊天会话列表"""
        await self.get_or_create_third_party_user(third_party_user_id)

        query = select(Chat).filter(Chat.third_party_user_id == third_party_user_id)

        if kb_id is not None:
            query = query.filter(Chat.knowledge_base_id == kb_id)

        if not include_deleted:
            query = query.filter(Chat.is_deleted == False)

        query = query.order_by(Chat.updated_at.desc()).offset(skip).limit(limit)

        chats = (await self.db.execute(query)).scalars().all()

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

        chat.last_message_at = datetime.now()

        await self.db.commit()
        await self.db.refresh(message)

        await self._cache_message(message)
        await self._cache_chat(chat)

        return message

    async def get_chat_messages(
            self,
            chat_id: int,
            user_id: int,
            skip: int = 0,
            limit: int = 50
    ) -> List[ChatMessage]:
        """获取聊天消息历史"""
        await self.get_chat(chat_id)

        messages = (await self.db.execute(
            select(ChatMessage)
            .filter(ChatMessage.chat_id == chat_id)
            .options(selectinload(ChatMessage.read_by))
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
        """软删除聊天会话"""
        chat = await self.get_chat(chat_id)

        chat.is_deleted = True
        chat.deleted_at = datetime.now()
        await self.db.commit()

        Logger.info(f"Soft deleted chat {chat_id}")

    async def list_admin_chats(
            self,
            admin_id: int,
            skip: int = 0,
            limit: int = 20,
            include_inactive: bool = False,
            all_chats: bool = False
    ) -> Tuple[List[Chat], int]:
        """获取管理员可见的聊天会话列表"""
        admin_user = await self.db.get(User, admin_id)
        if not admin_user or not admin_user.is_admin:
            raise HTTPException(status_code=403, detail="Only admin can access this endpoint")

        base_query = select(Chat)
        if not all_chats:
            base_query = base_query.filter(
                or_(
                    Chat.current_admin_id == admin_id,
                    Chat.current_admin_id == None
                )
            )

        if not include_inactive:
            base_query = base_query.filter(Chat.is_active == True)

        # Get total count before pagination
        total_query = select(func.count()).select_from(base_query.alias())
        total = (await self.db.execute(total_query)).scalar_one()

        # Subquery to calculate unread messages for the admin
        unread_count_subquery = (
            select(
                ChatMessage.chat_id,
                func.count(ChatMessage.id).label("unread_count")
            )
            .outerjoin(
                message_read_status,
                and_(
                    message_read_status.c.message_id == ChatMessage.id,
                    message_read_status.c.identity_id == admin_user.identity_id
                )
            )
            .filter(ChatMessage.message_type == MessageType.USER)  # Only count user messages as unread
            .filter(message_read_status.c.message_id == None)  # Filter for messages not read by the admin
            .group_by(ChatMessage.chat_id)
            .subquery()
        )

        # Main query to fetch chats and their unread counts
        final_query = (
            select(Chat, func.coalesce(unread_count_subquery.c.unread_count, 0).label("unread_count"))
            .select_from(base_query.alias())
            .outerjoin(unread_count_subquery, Chat.id == unread_count_subquery.c.chat_id)
            .options(selectinload(Chat.third_party_user))
            .order_by(desc(Chat.last_message_at))
            .offset(skip)
            .limit(limit)
        )

        results = (await self.db.execute(final_query)).all()

        chats = []
        for chat, unread_count in results:
            chat.unread_count = unread_count
            chats.append(chat)

        return chats, total

    async def switch_chat_mode(
            self,
            chat_id: int,
            admin_id: int,
            mode: ChatMode
    ) -> Chat:
        """切换聊天模式"""
        chat = await self.get_chat(chat_id)

        admin = await self.db.get(User, admin_id)
        if not admin or not admin.is_admin:
            raise HTTPException(status_code=403, detail="Only admin can switch chat mode")

        if mode == ChatMode.HUMAN:
            chat.chat_mode = ChatMode.HUMAN
            chat.current_admin_id = admin_id
            await self.add_system_message(chat_id=chat_id, content="已切换到人工服务模式")
        else:
            chat.chat_mode = ChatMode.AI
            chat.current_admin_id = None
            await self.add_system_message(chat_id=chat_id, content="已切换到AI助手模式")

        await self.db.commit()
        await self._cache_chat(chat)
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
            identity_id: int,
            message_ids: List[int]
    ) -> bool:
        """将指定消息标记为某个用户身份已读。"""
        if not message_ids:
            return False

        identity = await self.db.get(UserIdentity, identity_id)
        if not identity:
            Logger.warning(f"Attempted to mark messages as read for non-existent identity ID: {identity_id}")
            return False

        messages_to_update = await self.db.execute(
            select(ChatMessage)
            .options(selectinload(ChatMessage.read_by))
            .filter(ChatMessage.id.in_(message_ids), ChatMessage.chat_id == chat_id)
        )
        messages = messages_to_update.scalars().all()

        updated = False
        for message in messages:
            if identity not in message.read_by:
                message.read_by.append(identity)
                updated = True

        if updated:
            await self.db.commit()
            Logger.info(f"Identity {identity_id} marked {len(messages)} messages as read in chat {chat_id}")

        return updated

    async def list_messages(
            self,
            chat_id: int,
            page: int = 1,
            page_size: int = 50
    ) -> Tuple[List[ChatMessage], int]:
        """获取消息列表，支持分页"""
        query = select(ChatMessage).filter(
            ChatMessage.chat_id == chat_id
        ).order_by(desc(ChatMessage.created_at))

        total_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(total_query)).scalar_one()

        paged_query = query.offset((page - 1) * page_size).limit(page_size)
        messages = (await self.db.execute(paged_query)).scalars().all()

        return messages, total