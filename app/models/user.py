from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
from .knowledge_base import knowledge_base_users

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    sdk_key = Column(String, unique=True, index=True)
    secret_key = Column(String)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    # 关系定义
    created_by = relationship("User", remote_side=[id], backref="created_users")
    owned_knowledge_bases = relationship("KnowledgeBase", back_populates="owner", foreign_keys="KnowledgeBase.owner_id")
    knowledge_bases = relationship("KnowledgeBase", 
                                 secondary=knowledge_base_users,
                                 back_populates="users")
    # accessible_knowledge_bases 通过 KnowledgeBase 中的 backref 自动创建