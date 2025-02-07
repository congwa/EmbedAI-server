from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.services.auth import get_current_admin_user
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseUpdate
from app.services.knowledge_base import KnowledgeBaseService
from app.core.response import APIResponse

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/knowledge-bases")
async def create_knowledge_base(
    kb: KnowledgeBaseCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    kb_service = KnowledgeBaseService(db)
    result = await kb_service.create(kb, current_user.id)
    return APIResponse.success(data=result)

@router.put("/knowledge-bases/{kb_id}")
async def update_knowledge_base(
    kb_id: int,
    kb: KnowledgeBaseUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    kb_service = KnowledgeBaseService(db)
    result = await kb_service.update(kb_id, kb, current_user.id)
    return APIResponse.success(data=result)