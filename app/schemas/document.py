from typing import Optional
from pydantic import Field
from datetime import datetime
from .base import CustomBaseModel
from app.models.document import DocumentType

class DocumentBase(CustomBaseModel):
    """文档基础模型

    定义文档的基本字段
    """
    title: str = Field(..., min_length=1, max_length=255, description="文档标题")
    content: str = Field(..., min_length=1, description="文档内容")
    doc_type: DocumentType = Field(default=DocumentType.TEXT, description="文档类型")
    kb_id: int = Field(..., description="所属知识库ID")

class DocumentCreate(DocumentBase):
    """文档创建模型

    用于创建新文档时的请求数据验证
    """
    pass

class DocumentUpdate(CustomBaseModel):
    """文档更新模型

    用于更新文档时的请求数据验证
    所有字段都是可选的，只更新提供的字段
    """
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="文档标题")
    content: Optional[str] = Field(None, min_length=1, description="文档内容")
    doc_type: Optional[DocumentType] = Field(None, description="文档类型")

class DocumentInDB(DocumentBase):
    """数据库中的文档模型

    用于从数据库中读取的文档数据
    """
    id: int = Field(..., description="文档ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    user_id: int = Field(..., description="创建者ID")
    is_deleted: bool = Field(False, description="是否已删除")

class DocumentResponse(DocumentInDB):
    """文档响应模型

    用于API响应中的文档数据
    """
    pass

class DocumentPagination(CustomBaseModel):
    """文档分页响应模型

    用于返回分页的文档列表数据
    """
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    items: list[DocumentResponse] = Field(..., description="文档列表")