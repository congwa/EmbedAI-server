from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from .database import Base

class ThirdPartyUser(Base):
    """第三方用户模型
    
    用于标识使用知识库查询功能的外部用户：
    1. 不需要注册和认证
    2. 只需要前端生成的唯一ID
    3. 可以创建多个聊天会话
    4. 不能管理知识库和文档
    """
    __tablename__ = "third_party_users"
    __table_args__ = {'comment': '第三方用户表，用于标识使用查询功能的外部用户'}

    id = Column(Integer, primary_key=True, index=True, comment='用户ID')
    client_id = Column(String(100), nullable=True, index=True, comment='创建的时候的客户端ID，用于标识来源,作为保留字段，现在无作用')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    last_active_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='最后活跃时间')
    
    # 关系定义
    chats = relationship(
        "Chat", 
        back_populates="third_party_user", 
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    identities = relationship("UserIdentity", back_populates="third_party_user", passive_deletes=True)

    def __repr__(self):
        return f"<ThirdPartyUser {self.id}>" 