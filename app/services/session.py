from datetime import datetime, timedelta
from typing import Optional, List, Dict
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import json

from app.models.identity import UserIdentity, ChatSession
from app.models.chat import Chat
from app.core.redis_manager import redis_manager
from app.core.logger import Logger

class SessionManager:
    """会话管理器，用于处理用户身份和聊天会话的状态管理"""
    
    def __init__(self, db: Session):
        self.db = db
        self.session_expire_hours = 24  # 会话过期时间（小时）
        
    async def create_or_update_identity(
        self,
        client_id: str,
        third_party_user_id: Optional[int] = None,
        official_user_id: Optional[int] = None
    ) -> UserIdentity:
        """创建或更新用户身份"""
        # 查找现有身份
        query = select(UserIdentity).filter(
            UserIdentity.client_id == client_id
        )
        if third_party_user_id:
            query = query.filter(UserIdentity.third_party_user_id == third_party_user_id)
        if official_user_id:
            query = query.filter(UserIdentity.official_user_id == official_user_id)
            
        identity = (await self.db.execute(query)).scalar_one_or_none()
        
        if not identity:
            # 创建新身份
            identity = UserIdentity(
                client_id=client_id,
                third_party_user_id=third_party_user_id,
                official_user_id=official_user_id
            )
            self.db.add(identity)
        else:
            # 更新最后活跃时间
            identity.last_active_at = datetime.now()
            
        await self.db.commit()
        await self.db.refresh(identity)
        
        # 缓存身份信息
        await self._cache_identity(identity)
        
        return identity
        
    async def create_chat_session(
        self,
        chat_id: int,
        user_identity_id: int,
        client_id: str
    ) -> ChatSession:
        """创建新的聊天会话"""
        # 检查是否已存在活跃会话
        existing = await self.get_active_session(chat_id, client_id)
        if existing:
            return existing
            
        # 创建新会话
        session = ChatSession(
            chat_id=chat_id,
            user_identity_id=user_identity_id,
            client_id=client_id,
            expires_at=datetime.now() + timedelta(hours=self.session_expire_hours)
        )
        
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        
        # 缓存会话信息
        await self._cache_session(session)
        
        return session
        
    async def validate_session(
        self,
        chat_id: int,
        client_id: str,
        third_party_user_id: Optional[int] = None,
        official_user_id: Optional[int] = None
    ) -> bool:
        """验证会话有效性"""
        # 检查缓存
        session_key = f"session:{chat_id}:{client_id}"
        cached = await redis_manager.get(session_key)
        
        if cached:
            session_data = json.loads(cached)
            return (
                session_data["is_active"] and
                datetime.fromtimestamp(session_data["expires_at"]) > datetime.now()
            )
            
        # 从数据库查询
        query = select(ChatSession).filter(
            and_(
                ChatSession.chat_id == chat_id,
                ChatSession.client_id == client_id,
                ChatSession.is_active == True,
                ChatSession.expires_at > datetime.now()
            )
        )
        
        if third_party_user_id or official_user_id:
            identity_query = select(UserIdentity.id).filter(
                or_(
                    UserIdentity.third_party_user_id == third_party_user_id,
                    UserIdentity.official_user_id == official_user_id
                )
            )
            identity_ids = (await self.db.execute(identity_query)).scalars().all()
            if identity_ids:
                query = query.filter(ChatSession.user_identity_id.in_(identity_ids))
            else:
                return False
                
        session = (await self.db.execute(query)).scalar_one_or_none()
        
        if session:
            # 更新缓存
            await self._cache_session(session)
            return True
            
        return False
        
    async def get_active_session(
        self,
        chat_id: int,
        client_id: str
    ) -> Optional[ChatSession]:
        """获取活跃的聊天会话"""
        session = (await self.db.execute(
            select(ChatSession).filter(
                and_(
                    ChatSession.chat_id == chat_id,
                    ChatSession.client_id == client_id,
                    ChatSession.is_active == True,
                    ChatSession.expires_at > datetime.now()
                )
            )
        )).scalar_one_or_none()
        
        if session:
            # 更新最后活跃时间
            session.last_active_at = datetime.now()
            await self.db.commit()
            await self.db.refresh(session)
            
            # 更新缓存
            await self._cache_session(session)
            
        return session
        
    async def close_session(
        self,
        chat_id: int,
        client_id: str
    ) -> None:
        """关闭聊天会话"""
        session = await self.get_active_session(chat_id, client_id)
        if session:
            session.is_active = False
            await self.db.commit()
            
            # 删除缓存
            session_key = f"session:{chat_id}:{client_id}"
            await redis_manager.delete(session_key)
            
    async def cleanup_expired_sessions(self) -> None:
        """清理过期的会话"""
        expired = (await self.db.execute(
            select(ChatSession).filter(
                and_(
                    ChatSession.is_active == True,
                    ChatSession.expires_at <= datetime.now()
                )
            )
        )).scalars().all()
        
        for session in expired:
            session.is_active = False
            
        await self.db.commit()
        
        # 清理缓存
        for session in expired:
            session_key = f"session:{session.chat_id}:{session.client_id}"
            await redis_manager.delete(session_key)
            
    async def _cache_identity(self, identity: UserIdentity) -> None:
        """缓存用户身份信息"""
        identity_key = f"identity:{identity.id}"
        await redis_manager.set(
            identity_key,
            json.dumps({
                "id": identity.id,
                "client_id": identity.client_id,
                "third_party_user_id": identity.third_party_user_id,
                "official_user_id": identity.official_user_id,
                "is_active": identity.is_active,
                "last_active_at": identity.last_active_at
            }),
            expire=timedelta(hours=24)
        )
        
    async def _cache_session(self, session: ChatSession) -> None:
        """缓存会话信息"""
        session_key = f"session:{session.chat_id}:{session.client_id}"
        await redis_manager.set(
            session_key,
            json.dumps({
                "id": session.id,
                "chat_id": session.chat_id,
                "user_identity_id": session.user_identity_id,
                "client_id": session.client_id,
                "is_active": session.is_active,
                "last_active_at": session.last_active_at.timestamp(),
                "expires_at": session.expires_at.timestamp()
            }),
            expire=timedelta(hours=self.session_expire_hours)
        ) 