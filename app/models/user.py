from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime
from .associations import knowledge_base_users

class User(Base):
    """用户模型
    
    用于存储用户基本信息和认证信息
    支持邮箱登录和SDK认证
    """
    __tablename__ = "users"
    __table_args__ = {'comment': '用户表，存储用户基本信息和认证信息'}

    id = Column(Integer, primary_key=True, index=True, comment='用户ID')
    email = Column(String, unique=True, index=True, nullable=False, comment='用户邮箱，用于登录')
    hashed_password = Column(String, nullable=False, comment='加密后的密码')
    is_admin = Column(Boolean, default=False, comment='是否是管理员')
    is_active = Column(Boolean, default=True)
    sdk_key = Column(String, unique=True, nullable=True, comment='SDK密钥，用于客户端认证')
    secret_key = Column(String, nullable=True, comment='密钥，用于签名验证')
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    # 关系定义
    created_by = relationship("User", remote_side=[id], backref="created_users", passive_deletes=True)
    owned_knowledge_bases = relationship(
        "KnowledgeBase", 
        back_populates="owner", 
        foreign_keys="[KnowledgeBase.owner_id]",
        cascade="all, delete-orphan"
    )
    knowledge_bases = relationship(
        "KnowledgeBase",
        secondary=knowledge_base_users,
        back_populates="users",
        passive_deletes=True
    )
    # accessible_knowledge_bases 通过 KnowledgeBase 中的 backref 自动创建
    identities = relationship("UserIdentity", back_populates="official_user", passive_deletes=True)
    
    # 提示词模板关系
    prompt_templates = relationship("PromptTemplate", back_populates="owner", cascade="all, delete-orphan")


    def __repr__(self):
        return f"<User {self.email}>"