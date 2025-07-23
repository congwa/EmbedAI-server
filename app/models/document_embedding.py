from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from .database import Base

class DocumentEmbedding(Base):
    """文档向量模型，存储文档向量信息"""
    __tablename__ = "document_embeddings"
    __table_args__ = {'comment': '文档向量表，存储文档向量信息'}

    id = Column(Integer, primary_key=True, index=True, comment='向量ID')
    chunk_id = Column(Integer, ForeignKey("document_chunks.id", ondelete="CASCADE"), nullable=False, comment='分块ID')
    embedding = Column(JSON, nullable=False, comment='向量数据')
    model = Column(String, nullable=False, comment='嵌入模型')
    
    # 时间字段
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    
    # 关系定义
    chunk = relationship("DocumentChunk", back_populates="embeddings", passive_deletes=True)