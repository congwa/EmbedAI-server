from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.orm import Session, selectinload
from fastapi import HTTPException, status
from sqlalchemy.dialects.postgresql import insert
from app.models.chat import Chat, ChatMessage, MessageType, ChatUserLastRead
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

    async def get_user_identity_by_id(self, user_identity_id: int) -> Optional[UserIdentity]:
        """获取用户身份实例"""
        return (await self.db.execute(
            select(UserIdentity).filter(UserIdentity.id == user_identity_id)
        )).scalar_one_or_none()

    async def _cache_chat(self, chat: Chat) -> None:
        """缓存聊天会话信息到Redis"""
        await redis_manager.cache_chat(
            chat_id=chat.id,
            chat_data={
                "id": chat.id,
                "title": chat.title or "",
                "chat_mode": chat.chat_mode.value if chat.chat_mode else None,
                "is_active": chat.is_active,
                "third_party_user_id": chat.third_party_user_id,
                "knowledge_base_id": chat.knowledge_base_id,
                "current_admin_id": chat.current_admin_id or 0,
                "last_message_at": chat.last_message_at.strftime("%Y-%m-%d %H:%M:%S") if chat.last_message_at else None,
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )

    async def mark_messages_as_read(
        self,
        chat_id: int,
        user_identity_id: int,
        last_read_message_id: int
    ) -> None:
        """将用户的消息标记为已读"""
        user_identity = await self.get_user_identity_by_id(user_identity_id)
        if not user_identity:
            Logger.warning(f"标记已读失败：未找到用户身份 {user_identity_id}")
            return

        stmt = insert(ChatUserLastRead).values(
            chat_id=chat_id,
            user_identity_id=user_identity_id,
            last_read_message_id=last_read_message_id,
            updated_at=datetime.now()
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=['chat_id', 'user_identity_id'],
            set_=dict(last_read_message_id=last_read_message_id, updated_at=datetime.now())
        )
        await self.db.execute(stmt)

        messages_to_mark = (await self.db.execute(
            select(ChatMessage)
            .options(selectinload(ChatMessage.read_by))
            .filter(
                ChatMessage.chat_id == chat_id,
                ChatMessage.id <= last_read_message_id
            )
        )).scalars().all()

        for message in messages_to_mark:
            if user_identity not in message.read_by:
                message.read_by.append(user_identity)

        await self.db.commit()
        Logger.info(f"用户 {user_identity_id} 在会话 {chat_id} 中已读消息至 {last_read_message_id}")

    async def get_or_create_third_party_user(self, third_party_user_id: int) -> ThirdPartyUser:
        """获取或创建第三方用户"""
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
        """创建新的聊天会话"""
        await self.get_or_create_third_party_user(third_party_user_id)

        chat = Chat(
            third_party_user_id=third_party_user_id,
            knowledge_base_id=kb_id,
            title=title,
            messages=[]
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
        """获取聊天会话"""
        cached_chat_data = await self._get_cached_chat(chat_id)
        if cached_chat_data:
            # Manually construct a Chat object from cached data
            return Chat(**cached_chat_data)

        chat = (await self.db.execute(
            select(Chat).filter(Chat.id == chat_id)
        )).scalar_one_or_none()

        if not chat:
            Logger.warning(f"Chat {chat_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="聊天会话不存在"
            )

        await self._cache_chat(chat)
        return chat

    async def send_message(
            self,
            chat_id: int,
            content: str,
            message_type: MessageType,
            sender_id: Optional[int] = None,
            doc_metadata: Optional[dict] = None,
            sender_identity_id: Optional[int] = None
    ) -> ChatMessage:
        """添加新消息"""
        chat = await self.get_chat(chat_id)

        new_message = ChatMessage(
            chat_id=chat_id,
            content=content,
            message_type=message_type,
            sender_id=sender_id,
            doc_metadata=doc_metadata,
            created_at=datetime.now()
        )
        self.db.add(new_message)
        await self.db.commit()
        await self.db.refresh(new_message)

        chat.last_message_at = new_message.created_at

        if sender_identity_id:
            sender_identity = await self.get_user_identity_by_id(sender_identity_id)
            if sender_identity:
                new_message.read_by.append(sender_identity)
                # Also update the last read for the sender
                await self.mark_messages_as_read(chat_id, sender_identity_id, new_message.id)

        await self.db.commit()
        await self.db.refresh(chat)
        await self.db.refresh(new_message)

        await self._cache_chat(chat)

        return new_message

    async def get_messages(
            self,
            chat_id: int,
            user_identity_id: Optional[int] = None,
            page: int = 1,
            page_size: int = 20
    ) -> Dict[str, Any]:
        """获取消息列表，支持分页，并返回用户的已读位置"""
        query = (
            select(ChatMessage)
            .filter(ChatMessage.chat_id == chat_id)
            .options(selectinload(ChatMessage.read_by))
            .order_by(desc(ChatMessage.created_at))
        )

        total = (await self.db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()

        last_read_message_id = None
        if user_identity_id:
            last_read = (await self.db.execute(
                select(ChatUserLastRead.last_read_message_id)
                .filter(
                    ChatUserLastRead.chat_id == chat_id,
                    ChatUserLastRead.user_identity_id == user_identity_id
                )
            )).scalar_one_or_none()
            if last_read:
                last_read_message_id = last_read

        paged_query = query.offset((page - 1) * page_size).limit(page_size)
        messages = (await self.db.execute(paged_query)).scalars().all()

        return {
            "messages": messages,
            "total": total,
            "page": page,
            "page_size": page_size,
            "last_read_message_id": last_read_message_id
        }