from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum as SQLAlchemyEnum
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

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, comment="文档标题")
    content = Column(String, nullable=False, comment="文档内容")
    doc_type = Column(SQLAlchemyEnum(DocumentType), nullable=False, comment="文档类型")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    is_deleted = Column(Boolean, default=False, comment="是否删除")
    
    # 外键关联
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 关系
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    created_by = relationship("User")

    def __repr__(self):
        return f"<Document {self.title}>"