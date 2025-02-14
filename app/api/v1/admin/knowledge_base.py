from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.services.auth import get_current_admin_user, get_current_user
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBasePermissionCreate,
    KnowledgeBasePermissionUpdate
)
from app.services.knowledge_base import KnowledgeBaseService
from app.core.response import APIResponse

router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-base"])

@router.post("")
async def create_knowledge_base(
    kb: KnowledgeBaseCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """创建新的知识库

    Args:
        kb (KnowledgeBaseCreate): 知识库创建模型，包含知识库的基本信息
        db (Session): 数据库会话对象
        current_user: 当前登录用户

    Returns:
        APIResponse: 包含创建成功的知识库信息的响应对象
    """
    kb_service = KnowledgeBaseService(db)
    result = await kb_service.create(kb, current_user.id)
    return APIResponse.success(data=result)

@router.put("/{kb_id}")
async def update_knowledge_base(
    kb_id: int,
    kb: KnowledgeBaseUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新知识库信息

    Args:
        kb_id (int): 要更新的知识库ID
        kb (KnowledgeBaseUpdate): 知识库更新模型
        db (Session): 数据库会话对象
        current_user: 当前登录用户

    Returns:
        APIResponse: 包含更新后的知识库信息的响应对象
    """
    kb_service = KnowledgeBaseService(db)
    result = await kb_service.update(kb_id, kb, current_user.id)
    return APIResponse.success(data=result)

@router.post("/{kb_id}/train")
async def train_knowledge_base(
    kb_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """训练知识库

    Args:
        kb_id (int): 要训练的知识库ID
        db (Session): 数据库会话对象
        current_user: 当前登录用户

    Returns:
        APIResponse: 包含训练状态的响应对象
    """
    kb_service = KnowledgeBaseService(db)
    result = await kb_service.train(kb_id, current_user.id)
    return APIResponse.success(data=result)

@router.post("/{kb_id}/users")
async def add_user_to_knowledge_base(
    kb_id: int,
    permission: KnowledgeBasePermissionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """添加用户到知识库

    Args:
        kb_id (int): 知识库ID
        permission (KnowledgeBasePermissionCreate): 用户权限信息
        db (Session): 数据库会话对象
        current_user: 当前登录用户

    Returns:
        APIResponse: 操作结果响应
    """
    kb_service = KnowledgeBaseService(db)
    await kb_service.add_user(kb_id, permission, current_user.id)
    return APIResponse.success(message="用户添加成功")

@router.put("/{kb_id}/users/{user_id}")
async def update_user_permission(
    kb_id: int,
    user_id: int,
    permission: KnowledgeBasePermissionUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新用户的知识库权限

    Args:
        kb_id (int): 知识库ID
        user_id (int): 用户ID
        permission (KnowledgeBasePermissionUpdate): 新的权限信息
        db (Session): 数据库会话对象
        current_user: 当前登录用户

    Returns:
        APIResponse: 操作结果响应
    """
    kb_service = KnowledgeBaseService(db)
    await kb_service.update_user_permission(kb_id, user_id, permission, current_user.id)
    return APIResponse.success(message="权限更新成功")

@router.delete("/{kb_id}/users/{user_id}")
async def remove_user_from_knowledge_base(
    kb_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """从知识库中移除用户

    Args:
        kb_id (int): 知识库ID
        user_id (int): 要移除的用户ID
        db (Session): 数据库会话对象
        current_user: 当前登录用户

    Returns:
        APIResponse: 操作结果响应
    """
    kb_service = KnowledgeBaseService(db)
    await kb_service.remove_user(kb_id, user_id, current_user.id)
    return APIResponse.success(message="用户移除成功")

@router.get("/my")
async def list_my_knowledge_bases(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取当前用户可访问的所有知识库

    Args:
        db (Session): 数据库会话对象
        current_user: 当前登录用户

    Returns:
        APIResponse: 包含知识库列表的响应对象
    """
    kb_service = KnowledgeBaseService(db)
    result = await kb_service.get_user_knowledge_bases(current_user.id)
    return APIResponse.success(data=result) 