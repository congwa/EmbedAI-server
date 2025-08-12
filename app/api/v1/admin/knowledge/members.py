"""
知识库成员管理相关API
包含添加、删除、更新成员权限等操作
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import get_db
from app.services.auth import get_current_user
from app.schemas.knowledge_base import (
    KnowledgeBasePermissionCreate,
    KnowledgeBasePermissionUpdate,
    KnowledgeBaseMemberCreate,
    KnowledgeBaseMemberUpdate
)
from app.services.knowledge_base import KnowledgeBaseService
from app.core.response_utils import success_response
from app.models.user import User
from app.core.decorators import require_knowledge_base_permission
from app.models.enums import PermissionType
from app.core.logger import Logger

router = APIRouter()


@router.post("/{kb_id}/users")
async def add_user_to_knowledge_base(
    kb_id: int,
    permission: KnowledgeBasePermissionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """添加用户到知识库

    Args:
        kb_id (int): 知识库ID
        permission (KnowledgeBasePermissionCreate): 用户权限信息
        current_user: 当前登录用户
        db (AsyncSession): 数据库会话对象

    Returns:
        APIResponse: 操作结果响应
    """
    kb_service = KnowledgeBaseService(db)
    await kb_service.add_user(kb_id, permission, current_user.id)
    return success_response()


@router.put("/{kb_id}/users/{user_id}")
async def update_user_permission(
    kb_id: int,
    user_id: int,
    permission: KnowledgeBasePermissionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新用户的知识库权限

    Args:
        kb_id (int): 知识库ID
        user_id (int): 用户ID
        permission (KnowledgeBasePermissionUpdate): 新的权限信息
        current_user: 当前登录用户
        db (AsyncSession): 数据库会话对象

    Returns:
        APIResponse: 操作结果响应
    """
    kb_service = KnowledgeBaseService(db)
    await kb_service.update_user_permission(kb_id, user_id, permission, current_user.id)
    return success_response()


@router.delete("/{kb_id}/users/{user_id}")
async def remove_user_from_knowledge_base(
    kb_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """从知识库中移除用户

    Args:
        kb_id (int): 知识库ID
        user_id (int): 要移除的用户ID
        current_user: 当前登录用户
        db (AsyncSession): 数据库会话对象

    Returns:
        APIResponse: 操作结果响应
    """
    kb_service = KnowledgeBaseService(db)
    await kb_service.remove_user(kb_id, user_id, current_user.id)
    return success_response()


@router.get("/{kb_id}/members")
@require_knowledge_base_permission(PermissionType.VIEWER)
async def list_knowledge_base_members(
    kb_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取知识库成员列表

    Args:
        kb_id (int): 知识库ID
        current_user: 当前登录用户
        db (AsyncSession): 数据库会话对象

    Returns:
        APIResponse: 包含成员列表的响应对象
    """
    kb_service = KnowledgeBaseService(db)
    result = await kb_service.get_knowledge_base_members(kb_id, current_user.id)
    return success_response(data=result)


@router.post("/{kb_id}/members")
@require_knowledge_base_permission(PermissionType.ADMIN)
async def add_knowledge_base_member(
    kb_id: int,
    member_data: KnowledgeBaseMemberCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """添加知识库成员
    
    Args:
        kb_id: 知识库ID
        member_data: 成员信息
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        APIResponse: 成功响应
    """
    kb_service = KnowledgeBaseService(db)
    await kb_service.add_knowledge_base_member(kb_id, member_data, current_user.id)
    return success_response(message="成员添加成功")


@router.put("/{kb_id}/members/{user_id}")
@require_knowledge_base_permission(PermissionType.ADMIN)
async def update_knowledge_base_member(
    kb_id: int,
    user_id: int,
    member_data: KnowledgeBaseMemberUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新知识库成员权限
    
    Args:
        kb_id: 知识库ID
        user_id: 目标用户ID
        member_data: 更新的权限信息
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        APIResponse: 成功响应
    """
    kb_service = KnowledgeBaseService(db)
    await kb_service.update_knowledge_base_member(kb_id, user_id, member_data, current_user.id)
    return success_response(message="成员权限更新成功")


@router.delete("/{kb_id}/members/{user_id}")
@require_knowledge_base_permission(PermissionType.ADMIN)
async def remove_knowledge_base_member(
    kb_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """移除知识库成员
    
    Args:
        kb_id: 知识库ID
        user_id: 要移除的用户ID
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        APIResponse: 成功响应
    """
    kb_service = KnowledgeBaseService(db)
    await kb_service.remove_knowledge_base_member(kb_id, user_id, current_user.id)
    return success_response(message="成员移除成功") 