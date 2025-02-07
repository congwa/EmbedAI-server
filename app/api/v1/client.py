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
    kb_service = KnowledgeBaseService(db)
    result = await kb_service.query(kb_id, request)
    return APIResponse.success(data=result)