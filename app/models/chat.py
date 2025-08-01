from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Enum as SQLAlchemyEnum, Index, Boolean
from sqlalchemy.orm import relationship
from .database import Base
from .enums import ChatMode, MessageType
from .associations import message_read_status

class Chat(Base):
    """聊天会话模型"""
    __tablename__ = "chats"
    __table_args__ = (
        Index('idx_user_kb', 'third_party_user_id', 'knowledge_base_id'),
        Index('idx_updated_at', 'updated_at')
    )

    id = Column(Integer, primary_key=True, index=True, comment='会话ID')
    title = Column(String(255), nullable=True, comment='会话标题，默认为第一条用户消息')
    chat_mode = Column(SQLAlchemyEnum(ChatMode), default=ChatMode.AI, comment='聊天模式')
    is_active = Column(Boolean, default=True, comment='是否活跃')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    is_deleted = Column(Boolean, default=False, comment='是否已删除')
    deleted_at = Column(DateTime, nullable=True, comment='删除时间')
    last_message_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='最后消息时间')
    
    third_party_user_id = Column(Integer, ForeignKey("third_party_users.id", ondelete="CASCADE"), nullable=False, comment='第三方用户ID')
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False, comment='知识库ID')
    current_admin_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment='当前服务的管理员ID')
    
    third_party_user = relationship("ThirdPartyUser", back_populates="chats")
    knowledge_base = relationship("KnowledgeBase", back_populates="chats")
    current_admin = relationship("User", foreign_keys=[current_admin_id])
    messages = relationship("ChatMessage", back_populates="chat", cascade="all, delete-orphan", order_by="ChatMessage.created_at")
    sessions = relationship("ChatSession", back_populates="chat", cascade="all, delete-orphan")
    user_last_read = relationship("ChatUserLastRead", back_populates="chat", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Chat {self.id}: {self.title}>"

class ChatMessage(Base):
    """聊天消息模型"""
    __tablename__ = "chat_messages"
    __table_args__ = (
        Index('idx_message_created_at', 'created_at'),
    )

    id = Column(Integer, primary_key=True, index=True, comment='消息ID')
    content = Column(String, nullable=False, comment='消息内容')
    message_type = Column(SQLAlchemyEnum(MessageType), nullable=False, comment='消息类型')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    doc_metadata = Column(JSON, nullable=True, comment='消息元数据，如相关文档引用等')
    
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, comment='所属会话ID')
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment='发送者ID（管理员）')
    
    chat = relationship("Chat", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])
    read_by = relationship("UserIdentity", secondary=message_read_status, back_populates="read_messages", lazy="selectin")

    def __repr__(self):
        return f"<ChatMessage {self.id}: {self.message_type}>"

    def to_json(self):
        """Converts the message object to a JSON string."""
        import json
        
        read_by_list = []
        if self.read_by:
            for identity in self.read_by:
                if identity.official_user_id:
                    read_by_list.append({
                        "user_id": identity.official_user_id,
                        "user_type": "official",
                        "client_id": identity.client_id
                    })
                elif identity.third_party_user_id:
                    read_by_list.append({
                        "user_id": identity.third_party_user_id,
                        "user_type": "third_party",
                        "client_id": identity.client_id
                    })

        return json.dumps({
            "id": self.id,
            "chat_id": self.chat_id,
            "content": self.content,
            "message_type": self.message_type.value,
            "created_at": self.created_at.isoformat(),
            "sender": {
                "user_id": self.sender.id if self.sender else None,
                "user_type": "official" if self.sender else "system"
            },
            "doc_metadata": self.doc_metadata,
            "read_by": read_by_list
        })

class ChatSession(Base):
    """聊天会话参与者与状态模型"""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True, comment='会话记录ID')
    is_online = Column(Boolean, default=False, comment='是否在线')
    joined_at = Column(DateTime, default=datetime.now, comment='加入时间')
    left_at = Column(DateTime, nullable=True, comment='离开时间')
    
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, comment='所属会话ID')
    user_identity_id = Column(Integer, ForeignKey("user_identities.id", ondelete="CASCADE"), nullable=False, comment='用户身份ID')
    
    chat = relationship("Chat", back_populates="sessions")
    user_identity = relationship("UserIdentity", back_populates="chat_sessions")

    def __repr__(self):
        return f"<ChatSession chat={self.chat_id} user={self.user_identity_id}>"

class ChatUserLastRead(Base):
    """跟踪用户在会话中的最后已读消息ID"""
    __tablename__ = 'chat_user_last_read'
    __table_args__ = (
        Index('idx_user_chat_last_read', 'user_identity_id', 'chat_id', unique=True),
    )

    id = Column(Integer, primary_key=True)
    user_identity_id = Column(Integer, ForeignKey('user_identities.id', ondelete="CASCADE"), nullable=False)
    chat_id = Column(Integer, ForeignKey('chats.id', ondelete="CASCADE"), nullable=False)
    last_read_message_id = Column(Integer, ForeignKey('chat_messages.id', ondelete="SET NULL"), nullable=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user_identity = relationship("UserIdentity", back_populates="last_read_chats")
    chat = relationship("Chat", back_populates="user_last_read")
    last_read_message = relationship("ChatMessage")

    def __repr__(self):
        return f"<ChatUserLastRead user={self.user_identity_id} chat={self.chat_id} last_read={self.last_read_message_id}>"