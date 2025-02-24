from typing import Optional
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session
from app.core.response import APIResponse
from app.models.user import User
from app.models.database import get_db
from app.services.document import DocumentService
from app.schemas.document import DocumentCreate, DocumentUpdate, DocumentPagination, DocumentResponse
from app.services.auth import get_current_admin_user, get_current_user
from app.schemas.document import DocumentType
from datetime import datetime

router = APIRouter(tags=["admin"])

@router.post("/knowledge-bases/{kb_id}/documents")
async def create_document(
    *,
    doc_in: DocumentCreate,
    kb_id: int = Path(..., description="知识库ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建新文档

    Args:
        doc_in (DocumentCreate): 文档创建模型
        kb_id (int): 知识库ID
        current_user (User): 当前用户
        db (Session): 数据库会话

    Returns:
        APIResponse: 统一响应格式，包含创建的文档信息
    """
    document_service = DocumentService(db)
    doc = await document_service.create(doc_in, kb_id, current_user.id)
    return APIResponse.success(data=DocumentResponse.model_validate(doc))

@router.get("/knowledge-bases/{kb_id}/documents")
async def get_documents(
    kb_id: int = Path(..., description="知识库ID"),
    skip: int = Query(0, description="分页偏移量"),
    limit: int = Query(10, description="每页数量"),
    title: Optional[str] = Query(None, description="文档标题（模糊搜索）"),
    doc_type: Optional[DocumentType] = Query(None, description="文档类型"),
    start_time: Optional[datetime] = Query(None, description="创建时间范围开始"),
    end_time: Optional[datetime] = Query(None, description="创建时间范围结束"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取文档列表

    Args:
        kb_id (int): 知识库ID
        skip (int, optional): 分页偏移量. Defaults to 0.
        limit (int, optional): 每页数量. Defaults to 10.
        db (Session): 数据库会话

    Returns:
        APIResponse[DocumentPagination]: 统一响应格式，包含分页的文档列表
    """
    document_service = DocumentService(db)
    docs = await document_service.get_multi(
        knowledge_base_id=kb_id,
        skip=skip,
        limit=limit,
        title=title,
        doc_type=doc_type,
        start_time=start_time,
        end_time=end_time
    )
    
    # 将Document对象转换为DocumentResponse
    pagination_data = {
        "total": docs["total"],
        "page": skip // limit + 1,
        "page_size": limit,
        "items": [DocumentResponse.model_validate(doc) for doc in docs["items"]]
    }
    
    return APIResponse.success(data=DocumentPagination.model_validate(pagination_data))

@router.put("/documents/{doc_id}")
async def update_document(
    doc_id: int,
    doc_in: DocumentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新文档

    Args:
        doc_id (int): 文档ID
        doc_in (DocumentUpdate): 文档更新模型
        db (Session): 数据库会话

    Returns:
        APIResponse: 统一响应格式，包含更新后的文档信息
    """
    document_service = DocumentService(db)
    doc = await document_service.update(doc_id, doc_in)
    return APIResponse.success(data=DocumentResponse.model_validate(doc))

@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """软删除文档

    Args:
        doc_id (int): 文档ID
        db (Session): 数据库会话

    Returns:
        APIResponse: 统一响应格式
    """
    document_service = DocumentService(db)
    await document_service.delete(doc_id)
    return APIResponse.success(data={"message": "文档已删除"})

@router.get("/documents/{doc_id}")
async def get_document(
    doc_id: int = Path(..., description="文档ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取单个文档详情

    Args:
        doc_id (int): 文档ID
        current_user (User): 当前用户
        db (Session): 数据库会话

    Returns:
        APIResponse: 统一响应格式，包含文档详情
    """
    document_service = DocumentService(db)
    doc = await document_service.get(doc_id)
    return APIResponse.success(data=DocumentResponse.model_validate(doc))