from sqlalchemy import Column, Integer, String, ForeignKey, JSON, ARRAY, DateTime, Enum
from sqlalchemy.orm import relationship
from .database import Base
from enum import Enum as PyEnum

class TrainingStatus(PyEnum):
    INIT = "init"
    QUEUED = "queued"
    TRAINING = "training"
    TRAINED = "trained"
    FAILED = "failed"

class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), unique=True)
    domain = Column(String, default="通用知识领域")
    example_queries = Column(ARRAY(String), default=[])
    entity_types = Column(ARRAY(String), default=[])
    model_config = Column(JSON)
    working_dir = Column(String)
    
    # 训练相关字段
    training_status = Column(Enum(TrainingStatus), default=TrainingStatus.INIT)
    training_started_at = Column(DateTime, nullable=True)
    training_finished_at = Column(DateTime, nullable=True)
    training_error = Column(String, nullable=True)
    queued_at = Column(DateTime, nullable=True)
    
    owner = relationship("User", back_populates="knowledge_base", uselist=False)
    
    @property
    def can_train(self) -> bool:
        return self.training_status in [TrainingStatus.INIT, TrainingStatus.FAILED]
    
    @property
    def can_query(self) -> bool:
        return self.training_status == TrainingStatus.TRAINED