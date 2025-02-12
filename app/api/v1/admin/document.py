from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.response import APIResponse
from app.models.user import User
from app.models.database import get_db
from app.services.document import DocumentService
from app.schemas.document import DocumentCreate, DocumentUpdate, DocumentPagination
from app.services.auth import get_current_admin_user
from app.schemas.document import DocumentType
from datetime import datetime
from app.schemas.document import DocumentResponse

router = APIRouter(tags=["admin"])

@router.post("/documents", dependencies=[Depends(get_current_admin_user)])
async def create_document(
    *,
    doc_in: DocumentCreate,
    knowledge_base_id: int = Query(..., description="知识库ID"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """创建新文档（仅管理员）

    Args:
        doc_in (DocumentCreate): 文档创建模型
        knowledge_base_id (int): 知识库ID
        current_user (User): 当前管理员用户
        db (Session): 数据库会话

    Returns:
        APIResponse: 统一响应格式，包含创建的文档信息
    """
    document_service = DocumentService(db)
    doc = await document_service.create(doc_in, knowledge_base_id, current_user.id)
    return APIResponse.success(data=doc)

@router.get("/documents", dependencies=[Depends(get_current_admin_user)])
async def get_documents(
    knowledge_base_id: int = Query(..., description="知识库ID"),
    skip: int = Query(0, description="分页偏移量"),
    limit: int = Query(10, description="每页数量"),
    title: Optional[str] = Query(None, description="文档标题（模糊搜索）"),
    doc_type: Optional[DocumentType] = Query(None, description="文档类型"),
    start_time: Optional[datetime] = Query(None, description="创建时间范围开始"),
    end_time: Optional[datetime] = Query(None, description="创建时间范围结束"),
    db: Session = Depends(get_db)
):
    """获取文档列表（仅管理员）

    Args:
        knowledge_base_id (int): 知识库ID
        skip (int, optional): 分页偏移量. Defaults to 0.
        limit (int, optional): 每页数量. Defaults to 10.
        db (Session): 数据库会话

    Returns:
        APIResponse[DocumentPagination]: 统一响应格式，包含分页的文档列表
    """
    document_service = DocumentService(db)
    docs = await document_service.get_multi(
        knowledge_base_id=knowledge_base_id,
        skip=skip,
        limit=limit,
        title=title,
        doc_type=doc_type,
        start_time=start_time,
        end_time=end_time
    )
    return APIResponse.success(data=docs)

@router.put("/documents/{doc_id}", dependencies=[Depends(get_current_admin_user)])
async def update_document(
    doc_id: int,
    doc_in: DocumentUpdate,
    db: Session = Depends(get_db)
):
    """更新文档（仅管理员）

    Args:
        doc_id (int): 文档ID
        doc_in (DocumentUpdate): 文档更新模型
        db (Session): 数据库会话

    Returns:
        APIResponse: 统一响应格式，包含更新后的文档信息
    """
    document_service = DocumentService(db)
    doc = await document_service.update(doc_id, doc_in)
    return APIResponse.success(data=doc)

@router.delete("/documents/{doc_id}", dependencies=[Depends(get_current_admin_user)])
async def delete_document(
    doc_id: int,
    db: Session = Depends(get_db)
):
    """软删除文档（仅管理员）

    Args:
        doc_id (int): 文档ID
        db (Session): 数据库会话

    Returns:
        APIResponse: 统一响应格式，包含被删除的文档信息
    """
    document_service = DocumentService(db)
    doc = await document_service.delete(doc_id)
    return APIResponse.success(data=doc)