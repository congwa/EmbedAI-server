from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import get_db
from app.models.user import User
from app.core.auth import get_current_user
from app.services.knowledge_base import KnowledgeBaseService
from app.schemas.knowledge_base import QueryRequest, QueryResponse

router = APIRouter()

@router.post("/query/{kb_id}", response_model=QueryResponse)
async def query_knowledge_base(
    kb_id: int,
    query_request: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """查询知识库

    Args:
        kb_id (int): 知识库ID
        query_request (QueryRequest): 查询请求
        current_user (User): 当前用户
        db (AsyncSession): 数据库会话

    Returns:
        QueryResponse: 查询结果
    """
    kb_service = KnowledgeBaseService(db)
    result = await kb_service.query(kb_id, current_user.id, query_request.query, query_request.top_k)
    return result 