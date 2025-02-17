from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime
from .associations import knowledge_base_users

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    sdk_key = Column(String, unique=True, nullable=True)
    secret_key = Column(String, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系定义
    created_by = relationship("User", remote_side=[id], backref="created_users")
    owned_knowledge_bases = relationship(
        "KnowledgeBase", 
        back_populates="owner", 
        foreign_keys="KnowledgeBase.owner_id",
        cascade="all, delete-orphan"
    )
    knowledge_bases = relationship(
        "KnowledgeBase", 
        secondary=knowledge_base_users,
        back_populates="users",
        cascade="all, delete",
        passive_deletes=True
    )
    # accessible_knowledge_bases 通过 KnowledgeBase 中的 backref 自动创建