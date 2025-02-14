from sqlalchemy import Column, Integer, String, ForeignKey, JSON, ARRAY, DateTime, Enum, Table
from sqlalchemy.orm import relationship
from .database import Base
from enum import Enum as PyEnum
from datetime import datetime

class PermissionType(PyEnum):
    """权限类型"""
    OWNER = "owner"      # 所有者权限 完全控制权限
    ADMIN = "admin"      # 管理员权限 管理权限，可以管理其他用户的访问权限
    EDITOR = "editor"    # 编辑权限 编辑权限，可以添加/修改文档
    VIEWER = "viewer"    # 查看权限  查看权限，只能查看和使用

class TrainingStatus(PyEnum):
    INIT = "init"
    QUEUED = "queued"
    TRAINING = "training"
    TRAINED = "trained"
    FAILED = "failed"

# 知识库用户权限关联表
knowledge_base_users = Table(
    "knowledge_base_users",
    Base.metadata,
    Column("knowledge_base_id", Integer, ForeignKey("knowledge_bases.id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("permission", Enum(PermissionType), default=PermissionType.VIEWER),
    Column("created_at", DateTime, default=datetime.now),
)

class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))  # 移除 unique=True
    domain = Column(String, default="通用知识领域")
    example_queries = Column(JSON, default=lambda: [])
    entity_types = Column(JSON, default=lambda: [])
    llm_config = Column(JSON)
    working_dir = Column(String)
    
    # 训练相关字段
    training_status = Column(Enum(TrainingStatus), default=TrainingStatus.INIT)
    training_started_at = Column(DateTime, nullable=True)
    training_finished_at = Column(DateTime, nullable=True)
    training_error = Column(String, nullable=True)
    queued_at = Column(DateTime, nullable=True)
    
    # 关系定义
    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_knowledge_bases")
    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan")
    users = relationship("User", 
                        secondary=knowledge_base_users,
                        backref="accessible_knowledge_bases")
    
    @property
    def can_train(self) -> bool:
        return self.training_status in [TrainingStatus.INIT, TrainingStatus.FAILED]
    
    @property
    def can_query(self) -> bool:
        return self.training_status == TrainingStatus.TRAINED