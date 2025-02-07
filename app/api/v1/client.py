from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.services.auth import get_current_user
from app.schemas.knowledge_base import QueryRequest
from app.services.knowledge_base import KnowledgeBaseService
from app.core.response import APIResponse

router = APIRouter(tags=["client"])

@router.post("/query/{kb_id}")
async def query_knowledge_base(
    kb_id: int,
    request: QueryRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """查询知识库

    根据用户的查询请求，在指定的知识库中进行信息检索

    Args:
        kb_id (int): 要查询的知识库ID
        request (QueryRequest): 查询请求模型，包含查询的具体参数
        db (Session): 数据库会话对象
        current_user: 当前登录的用户

    Returns:
        APIResponse: 包含查询结果的响应对象
    """
    kb_service = KnowledgeBaseService(db)
    result = await kb_service.query(kb_id, request)
    return APIResponse.success(data=result)