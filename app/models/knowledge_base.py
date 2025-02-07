from sqlalchemy import Column, Integer, String, ForeignKey, JSON, ARRAY
from sqlalchemy.orm import relationship
from .database import Base

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
    
    owner = relationship("User", back_populates="knowledge_base", uselist=False)