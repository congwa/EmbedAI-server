from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum as SQLAlchemyEnum, JSON, LargeBinary
from sqlalchemy.orm import relationship
from app.models.database import Base
from typing import Optional, Dict, Any

class DocumentType(str, Enum):
    """文档类型枚举

    定义支持的各种文档类型
    """
    # 文本类型
    TEXT = "text"  # 纯文本
    MARKDOWN = "markdown"  # Markdown文档
    HTML = "html"  # HTML文档
    
    # 办公文档
    PDF = "pdf"  # PDF文档
    DOCX = "docx"  # Word文档
    DOC = "doc"  # 旧版Word文档
    XLSX = "xlsx"  # Excel文档
    XLS = "xls"  # 旧版Excel文档
    PPTX = "pptx"  # PowerPoint文档
    PPT = "ppt"  # 旧版PowerPoint文档
    
    # 编程相关
    PYTHON = "python"  # Python文件
    JAVASCRIPT = "javascript"  # JavaScript文件
    JAVA = "java"  # Java文件
    CPP = "cpp"  # C++文件
    CSHARP = "csharp"  # C#文件
    GO = "go"  # Go文件
    RUST = "rust"  # Rust文件
    
    # 数据格式
    JSON = "json"  # JSON文件
    XML = "xml"  # XML文件
    CSV = "csv"  # CSV文件
    
    # 其他
    IMAGE = "image"  # 图片文件
    AUDIO = "audio"  # 音频文件
    VIDEO = "video"  # 视频文件
    
    @classmethod
    def from_extension(cls, extension: str) -> 'DocumentType':
        """从文件扩展名获取文档类型"""
        extension = extension.lower().lstrip('.')
        type_map = {
            # 文本类型
            'txt': cls.TEXT,
            'md': cls.MARKDOWN,
            'markdown': cls.MARKDOWN,
            'html': cls.HTML,
            'htm': cls.HTML,
            
            # 办公文档
            'pdf': cls.PDF,
            'docx': cls.DOCX,
            'doc': cls.DOC,
            'xlsx': cls.XLSX,
            'xls': cls.XLS,
            'pptx': cls.PPTX,
            'ppt': cls.PPT,
            'odt': cls.DOCX,  # OpenDocument Text
            'ods': cls.XLSX,  # OpenDocument Spreadsheet
            'odp': cls.PPTX,  # OpenDocument Presentation
            
            # 编程相关
            'py': cls.PYTHON,
            'js': cls.JAVASCRIPT,
            'java': cls.JAVA,
            'cpp': cls.CPP,
            'c': cls.CPP,
            'h': cls.CPP,
            'cs': cls.CSHARP,
            'go': cls.GO,
            'rs': cls.RUST,
            
            # 数据格式
            'json': cls.JSON,
            'xml': cls.XML,
            'csv': cls.CSV,
            'tsv': cls.CSV,
            
            # 其他
            'jpg': cls.IMAGE,
            'jpeg': cls.IMAGE,
            'png': cls.IMAGE,
            'gif': cls.IMAGE,
            'bmp': cls.IMAGE,
            'webp': cls.IMAGE,
            'mp3': cls.AUDIO,
            'wav': cls.AUDIO,
            'ogg': cls.AUDIO,
            'mp4': cls.VIDEO,
            'avi': cls.VIDEO,
            'mov': cls.VIDEO,
        }
        return type_map.get(extension, cls.TEXT)

class Document(Base):
    """文档模型

    用于存储用户上传的文档信息
    实现软删除机制，删除操作只是标记状态而不真正删除数据
    """
    __tablename__ = "documents"
    __table_args__ = {'comment': '文档表，存储知识库的文档内容'}

    id = Column(Integer, primary_key=True, index=True, comment='文档ID')
    title = Column(String(255), nullable=False, comment='文档标题')
    content = Column(String, nullable=True, comment='文档内容（文本内容）')
    doc_type = Column(SQLAlchemyEnum(DocumentType), nullable=False, comment='文档类型')
    file_name = Column(String(512), nullable=True, comment='原始文件名')
    file_size = Column(Integer, nullable=True, comment='文件大小（字节）')
    file_hash = Column(String(64), nullable=True, index=True, comment='文件哈希值，用于去重')
    mime_type = Column(String(128), nullable=True, comment='文件MIME类型')
    
    # 文件存储相关
    storage_path = Column(String(512), nullable=True, comment='文件存储路径')
    storage_provider = Column(String(64), default='local', comment='存储提供者')
    storage_metadata = Column(JSON, nullable=True, comment='存储元数据')
    
    # 处理状态
    processing_status = Column(String(32), default='pending', comment='处理状态: pending, processing, completed, failed')
    processing_error = Column(String(1024), nullable=True, comment='处理错误信息')
    processed_at = Column(DateTime, nullable=True, comment='处理完成时间')
    
    # 元数据
    doc_metadata = Column(JSON, nullable=True, comment='文档元数据，存储额外的文档信息')
    source_url = Column(String(512), nullable=True, comment='文档来源URL')
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    is_deleted = Column(Boolean, default=False, comment='是否删除')
    deleted_at = Column(DateTime, nullable=True, comment='删除时间')
    
    # 外键关联，添加 ondelete 设置
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False, index=True, comment='所属知识库ID')
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True, comment='创建者用户ID')
    
    # 关系定义
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    created_by = relationship("User", passive_deletes=True)
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan", passive_deletes=True)
    
    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """更新文档元数据"""
        if self.doc_metadata is None:
            self.doc_metadata = {}
        self.doc_metadata.update(metadata)
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取文档元数据"""
        if not self.doc_metadata:
            return default
        return self.doc_metadata.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，用于序列化"""
        from app.schemas.document import Document as DocumentSchema
        schema = DocumentSchema.model_validate(self)
        return schema.model_dump(mode='json')
    
    @property
    def is_processed(self) -> bool:
        """文档是否已处理完成"""
        return self.processing_status == 'completed'
    
    @property
    def is_processing(self) -> bool:
        """文档是否正在处理中"""
        return self.processing_status == 'processing'
    
    @property
    def has_failed(self) -> bool:
        """文档处理是否失败"""
        return self.processing_status == 'failed'

    def __repr__(self):
        return f"<Document {self.title}>"