from datetime import datetime
from typing import Optional, Set
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.models.database import Base

class UserIdentity(Base):
    """用户身份模型，用于管理不同类型用户的身份信息"""
    __tablename__ = "user_identities"

    id = Column(Integer, primary_key=True, index=True)
    official_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    third_party_user_id = Column(Integer, ForeignKey("third_party_users.id"), nullable=True)
    client_id = Column(String, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    last_active_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    official_user = relationship("User", back_populates="identities")
    third_party_user = relationship("ThirdPartyUser", back_populates="identities")
    active_sessions = relationship("ChatSession", back_populates="user_identity")

class ChatSession(Base):
    """聊天会话状态模型"""
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), index=True)
    user_identity_id = Column(Integer, ForeignKey("user_identities.id"))
    client_id = Column(String, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    last_active_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    expires_at = Column(DateTime)

    # 关系
    chat = relationship("Chat", back_populates="sessions")
    user_identity = relationship("UserIdentity", back_populates="active_sessions") 