from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Enum as SQLAlchemyEnum, Index, Boolean
from sqlalchemy.orm import relationship
from .database import Base
from .enums import ChatMode, MessageType

class Chat(Base):
    """聊天会话模型
    
    用于存储第三方用户与知识库的聊天会话信息：
    1. 一个第三方用户可以与同一个知识库创建多个会话
    2. 每个会话包含多条消息记录
    3. 会话标题默认使用第一条用户消息
    4. 会话按最后更新时间排序
    5. 会话ID在全局范围内唯一
    6. 支持软删除，删除的会话不会真正从数据库中删除
    7. 支持AI模式和人工模式切换
    """
    __tablename__ = "chats"
    __table_args__ = (
        {'comment': '聊天会话表，存储第三方用户与知识库的会话信息'},
        # 创建联合索引，优化查询性能
        Index('idx_user_kb', 'third_party_user_id', 'knowledge_base_id'),
        # 创建更新时间索引，用于排序
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
    
    # 外键关联
    third_party_user_id = Column(Integer, ForeignKey("third_party_users.id", ondelete="CASCADE"), nullable=False, comment='第三方用户ID')
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False, comment='知识库ID')
    current_admin_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment='当前服务的管理员ID')
    
    # 关系定义
    third_party_user = relationship("ThirdPartyUser", back_populates="chats")
    knowledge_base = relationship("KnowledgeBase", back_populates="chats")
    current_admin = relationship("User", foreign_keys=[current_admin_id])
    messages = relationship("ChatMessage", back_populates="chat", cascade="all, delete-orphan", order_by="ChatMessage.created_at")

    def __repr__(self):
        return f"<Chat {self.id}: {self.title}>"

class ChatMessage(Base):
    """聊天消息模型
    
    存储聊天会话中的具体消息内容：
    1. 包括用户的问题、知识库的回答和管理员的回复
    2. 消息按创建时间排序
    3. 支持存储元数据（如相关文档引用）
    4. 支持消息已读状态
    """
    __tablename__ = "chat_messages"
    __table_args__ = (
        {'comment': '聊天消息表，存储会话中的具体消息'},
        # 创建消息创建时间索引，用于排序
        Index('idx_message_created_at', 'created_at')
    )

    id = Column(Integer, primary_key=True, index=True, comment='消息ID')
    content = Column(String, nullable=False, comment='消息内容')
    message_type = Column(SQLAlchemyEnum(MessageType), nullable=False, comment='消息类型')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    is_read = Column(Boolean, default=False, comment='是否已读')
    metadata = Column(JSON, nullable=True, comment='消息元数据，如相关文档引用等')
    
    # 外键关联
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, comment='所属会话ID')
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment='发送者ID（管理员）')
    
    # 关系定义
    chat = relationship("Chat", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])

    def __repr__(self):
        return f"<ChatMessage {self.id}: {self.message_type}>" 