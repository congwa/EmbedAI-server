from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum as SQLAlchemyEnum, JSON
from sqlalchemy.orm import relationship
from app.models.database import Base

class DocumentType(str, Enum):
    """文档类型枚举

    定义文档的类型，方便未来扩展更多类型
    """
    TEXT = "text"  # 文本文档
    # 未来可以在此处添加更多文档类型
    # PDF = "pdf"
    # WORD = "word"
    # 等等

class Document(Base):
    """文档模型

    用于存储用户上传的文档信息
    实现软删除机制，删除操作只是标记状态而不真正删除数据
    """
    __tablename__ = "documents"
    __table_args__ = {'comment': '文档表，存储知识库的文档内容'}

    id = Column(Integer, primary_key=True, index=True, comment='文档ID')
    title = Column(String(255), nullable=False, comment='文档标题')
    content = Column(String, nullable=False, comment='文档内容')
    doc_type = Column(SQLAlchemyEnum(DocumentType), nullable=False, comment='文档类型')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    is_deleted = Column(Boolean, default=False, comment='是否删除')
    deleted_at = Column(DateTime, nullable=True, comment='删除时间')
    doc_metadata = Column(JSON, nullable=True, comment='文档元数据，存储额外的文档信息')
    source_url = Column(String, nullable=True, comment='文档来源URL')
    
    # 外键关联，添加 ondelete 设置
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False, comment='所属知识库ID')
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment='创建者用户ID')
    
    # 关系定义
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    created_by = relationship("User", passive_deletes=True)

    def __repr__(self):
        return f"<Document {self.title}>"