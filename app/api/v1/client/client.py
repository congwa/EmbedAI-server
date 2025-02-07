from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.schemas.knowledge_base import QueryRequest
from app.services.knowledge_base import KnowledgeBaseService
from app.core.response import APIResponse
from app.utils.rate_limit import rate_limit
from app.core.decorators import require_sdk_auth
from datetime import timedelta

router = APIRouter(prefix="/client", tags=["client"])

@router.post("/query/{kb_id}")
@rate_limit(max_requests=100, time_window=timedelta(minutes=1))
@require_sdk_auth()
async def query_knowledge_base(
    kb_id: int,
    request: QueryRequest,
    db: Session = Depends(get_db)
):
    """查询知识库

    根据用户的查询请求，在指定的知识库中进行信息检索
    此接口为前台用户接口，需要SDK认证

    Args:
        kb_id (int): 要查询的知识库ID
        request (QueryRequest): 查询请求模型，包含查询的具体参数
        db (Session): 数据库会话对象

    Returns:
        APIResponse: 包含查询结果的响应对象
    """
    kb_service = KnowledgeBaseService(db)
    result = await kb_service.query(kb_id, request)
    return APIResponse.success(data=result)