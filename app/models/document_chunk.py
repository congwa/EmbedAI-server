from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from .database import Base

class DocumentChunk(Base):
    """文档分块模型，存储文档分块信息"""
    __tablename__ = "document_chunks"
    __table_args__ = {'comment': '文档分块表，存储文档分块信息'}

    id = Column(Integer, primary_key=True, index=True, comment='分块ID')
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, comment='文档ID')
    content = Column(Text, nullable=False, comment='分块内容')
    chunk_index = Column(Integer, nullable=False, comment='分块索引')
    chunk_metadata = Column(JSON, nullable=True, comment='分块元数据')
    
    # 时间字段
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    # 关系定义
    document = relationship("Document", back_populates="chunks", passive_deletes=True)
    embeddings = relationship("DocumentEmbedding", back_populates="chunk", cascade="all, delete-orphan", passive_deletes=True)