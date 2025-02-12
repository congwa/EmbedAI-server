from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.services.auth import get_current_admin_user
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseUpdate
from app.services.knowledge_base import KnowledgeBaseService
from app.core.response import APIResponse

router = APIRouter(prefix="/knowledge-bases", tags=["admin-knowledge-base"])

@router.post("", dependencies=[Depends(get_current_admin_user)])
async def create_knowledge_base(
    kb: KnowledgeBaseCreate,
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """创建新的知识库

    创建一个新的知识库记录，只有管理员用户可以执行此操作

    Args:
        kb (KnowledgeBaseCreate): 知识库创建模型，包含知识库的基本信息
        user_id (int): 要绑定的普通用户ID
        db (Session): 数据库会话对象
        current_user: 当前登录的管理员用户

    Returns:
        APIResponse: 包含创建成功的知识库信息的响应对象
    """
    kb_service = KnowledgeBaseService(db)
    result = await kb_service.create(kb, user_id)
    return APIResponse.success(data=result)

@router.put("/{kb_id}", dependencies=[Depends(get_current_admin_user)])
async def update_knowledge_base(
    kb_id: int,
    kb: KnowledgeBaseUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """更新知识库信息

    更新指定ID的知识库信息，只有管理员用户可以执行此操作

    Args:
        kb_id (int): 要更新的知识库ID
        kb (KnowledgeBaseUpdate): 知识库更新模型，包含需要更新的字段
        db (Session): 数据库会话对象
        current_user: 当前登录的管理员用户

    Returns:
        APIResponse: 包含更新后的知识库信息的响应对象
    """
    kb_service = KnowledgeBaseService(db)
    result = await kb_service.update(kb_id, kb, current_user.id)
    return APIResponse.success(data=result)

@router.post("/{kb_id}/train", dependencies=[Depends(get_current_admin_user)])
async def train_knowledge_base(
    kb_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """训练知识库

    启动指定ID的知识库训练过程，只有管理员用户可以执行此操作

    Args:
        kb_id (int): 要训练的知识库ID
        db (Session): 数据库会话对象
        current_user: 当前登录的管理员用户

    Returns:
        APIResponse: 包含训练状态的响应对象
    """
    kb_service = KnowledgeBaseService(db)
    result = await kb_service.train(kb_id)
    return APIResponse.success(data=result) 