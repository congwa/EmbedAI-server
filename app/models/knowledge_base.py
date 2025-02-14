from sqlalchemy import Column, Integer, String, ForeignKey, JSON, ARRAY, DateTime, Enum, Table
from sqlalchemy.orm import relationship
from .database import Base
from enum import Enum as PyEnum
from datetime import datetime
from typing import List, Dict, Any, Optional

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
    Column("permission", Enum(PermissionType), nullable=False),
    Column("created_at", DateTime, nullable=False, default=datetime.now)
)

class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    domain = Column(String, nullable=False)
    example_queries = Column(JSON, nullable=False)
    entity_types = Column(JSON, nullable=False)
    llm_config = Column(JSON, nullable=False)
    working_dir = Column(String, nullable=True)
    
    # 训练相关字段
    training_status = Column(Enum(TrainingStatus), nullable=False, default=TrainingStatus.INIT)
    training_started_at = Column(DateTime, nullable=True)
    training_finished_at = Column(DateTime, nullable=True)
    training_error = Column(String, nullable=True)
    queued_at = Column(DateTime, nullable=True)
    
    # 关系定义
    owner = relationship("User", back_populates="owned_knowledge_bases", foreign_keys=[owner_id])
    documents = relationship("Document", back_populates="knowledge_base")
    users = relationship("User", 
                        secondary=knowledge_base_users,
                        back_populates="knowledge_bases")
    
    @property
    def can_train(self) -> bool:
        return self.training_status in [TrainingStatus.INIT, TrainingStatus.FAILED]
    
    @property
    def can_query(self) -> bool:
        return self.training_status == TrainingStatus.TRAINED

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，用于 JSON 序列化"""
        return {
            'id': self.id,
            'name': self.name,
            'owner_id': self.owner_id,
            'domain': self.domain,
            'example_queries': self.example_queries,
            'entity_types': self.entity_types,
            'llm_config': self.llm_config,
            'working_dir': self.working_dir,
            'training_status': self.training_status.value,
            'training_started_at': self.training_started_at.isoformat() if self.training_started_at else None,
            'training_finished_at': self.training_finished_at.isoformat() if self.training_finished_at else None,
            'training_error': self.training_error,
            'queued_at': self.queued_at.isoformat() if self.queued_at else None,
            'can_train': self.can_train,
            'can_query': self.can_query
        }