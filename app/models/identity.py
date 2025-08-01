from datetime import datetime
from typing import Optional, Set
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.models.database import Base
from .associations import message_read_status

class UserIdentity(Base):
    """用户身份模型，用于管理不同类型用户的身份信息"""
    __tablename__ = "user_identities"

    id = Column(Integer, primary_key=True, index=True, comment='身份ID')
    official_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment='官方用户ID')
    third_party_user_id = Column(Integer, ForeignKey("third_party_users.id"), nullable=True, comment='第三方用户ID')
    client_id = Column(String, index=True, comment='客户端ID，用于标识连接的客户端')
    is_active = Column(Boolean, default=True, comment='身份是否活跃')
    created_at = Column(DateTime, default=datetime.now, comment='身份创建时间')
    last_active_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='身份最后活跃时间')

    # 关系
    official_user = relationship("User", back_populates="identities")
    third_party_user = relationship("ThirdPartyUser", back_populates="identities")
    active_sessions = relationship("ChatSession", back_populates="user_identity")
    read_messages = relationship("ChatMessage", secondary=message_read_status, back_populates="read_by")

class ChatSession(Base):
    """聊天会话状态模型，用于管理用户在聊天会话中的状态"""
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True, comment='会话状态ID')
    chat_id = Column(Integer, ForeignKey("chats.id"), index=True, comment='关联的聊天会话ID')
    user_identity_id = Column(Integer, ForeignKey("user_identities.id"), comment='关联的用户身份ID')
    client_id = Column(String, index=True, comment='客户端ID，用于标识连接的客户端')
    is_active = Column(Boolean, default=True, comment='会话状态是否活跃')
    created_at = Column(DateTime, default=datetime.now, comment='会话状态创建时间')
    last_active_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='会话状态最后活跃时间')
    expires_at = Column(DateTime, comment='会话状态过期时间')

    # 关系
    chat = relationship("Chat", back_populates="sessions")
    user_identity = relationship("UserIdentity", back_populates="active_sessions") 