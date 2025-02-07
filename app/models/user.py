from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

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

    # 关系定义
    created_by = relationship("User", remote_side=[id], backref="created_users")
    knowledge_base = relationship("KnowledgeBase", back_populates="owner", uselist=False)