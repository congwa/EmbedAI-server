from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.services.knowledge_base import KnowledgeBaseService
from app.services.session import SessionManager
from app.schemas.knowledge_base import QueryRequest, QueryResponse
from app.schemas.identity import UserContext, UserType
from app.core.logger import Logger
from app.core.response import ResponseModel, APIResponse

# 移除前缀，因为已在__init__.py中设置
router = APIRouter()

@router.post("/{kb_id}/query", response_model=ResponseModel[QueryResponse])
async def query_knowledge_base(
    kb_id: int,
    request: QueryRequest,
    client_id: str,
    third_party_user_id: int,
    db: Session = Depends(get_db)
):
    """第三方用户查询知识库"""
    try:
        # 创建用户上下文
        session_manager = SessionManager(db)
        identity = await session_manager.create_or_update_identity(
            client_id=client_id,
            third_party_user_id=third_party_user_id
        )
        
        user_context = UserContext(
            user_type=UserType.THIRD_PARTY,
            user_id=third_party_user_id,
            client_id=client_id,
            identity_id=identity.id
        )
        
        # 执行查询
        kb_service = KnowledgeBaseService(db)
        result = await kb_service.query(
            kb_id=kb_id,
            user_context=user_context,
            query=request.query,
            top_k=request.top_k
        )
        
        return APIResponse.success(data=QueryResponse(
            query=result["query"],
            results=result["results"],
            metadata=result["doc_metadata"]
        ))
        
    except Exception as e:
        Logger.error(f"Query failed: {str(e)}")
        return APIResponse.error(
            message=f"查询失败: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 
