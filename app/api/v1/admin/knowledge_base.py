from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import get_db
from app.services.auth import get_current_admin_user, get_current_user
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBasePermissionCreate,
    KnowledgeBasePermissionUpdate,
    KnowledgeBaseMemberCreate,
    KnowledgeBaseMemberUpdate
)
from app.services.knowledge_base import KnowledgeBaseService
from app.core.response import APIResponse
from app.models.user import User

router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-base"])

@router.post("")
async def create_knowledge_base(
    kb: KnowledgeBaseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建新的知识库

    Args:
        kb (KnowledgeBaseCreate): 知识库创建模型，包含知识库的基本信息
        current_user: 当前登录用户
        db (AsyncSession): 数据库会话对象

    Returns:
        APIResponse: 包含创建成功的知识库信息的响应对象
    """
    kb_service = KnowledgeBaseService(db)
    result = await kb_service.create(kb, current_user.id)
    return APIResponse.success(data=result.to_dict())

@router.put("/{kb_id}")
async def update_knowledge_base(
    kb_id: int,
    kb: KnowledgeBaseUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新知识库信息

    Args:
        kb_id (int): 要更新的知识库ID
        kb (KnowledgeBaseUpdate): 知识库更新模型
        current_user: 当前登录用户
        db (AsyncSession): 数据库会话对象

    Returns:
        APIResponse: 包含更新后的知识库信息的响应对象
    """
    kb_service = KnowledgeBaseService(db)
    result = await kb_service.update(kb_id, kb, current_user.id)
    return APIResponse.success(data=result.to_dict())

@router.post("/{kb_id}/train")
async def train_knowledge_base(
    kb_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """训练知识库

    Args:
        kb_id (int): 要训练的知识库ID
        current_user: 当前登录用户
        db (AsyncSession): 数据库会话对象

    Returns:
        APIResponse: 包含训练状态的响应对象
    """
    kb_service = KnowledgeBaseService(db)
    result = await kb_service.train(kb_id, current_user.id)
    return APIResponse.success(data=result.to_dict())

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
    return APIResponse.success()

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
    return APIResponse.success()

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
    return APIResponse.success()

@router.get("/my")
async def list_my_knowledge_bases(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户可访问的所有知识库，包含成员信息

    Args:
        current_user: 当前登录用户
        db (AsyncSession): 数据库会话对象

    Returns:
        APIResponse: 包含知识库列表的响应对象，每个知识库包含成员信息
    """
    kb_service = KnowledgeBaseService(db)
    result = await kb_service.get_user_knowledge_bases(current_user.id)
    return APIResponse.success(data=result)

@router.get("/{kb_id}")
async def get_knowledge_base(
    kb_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取知识库详情

    Args:
        kb_id (int): 知识库ID
        current_user: 当前登录用户
        db (AsyncSession): 数据库会话对象

    Returns:
        APIResponse: 包含知识库详情的响应对象
    """
    kb_service = KnowledgeBaseService(db)
    result = await kb_service.get(kb_id, current_user.id)
    return APIResponse.success(data=result.to_dict())

@router.post("/{kb_id}/query")
async def query_knowledge_base(
    kb_id: int,
    query_request: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """查询知识库

    Args:
        kb_id (int): 知识库ID
        query_request (dict): 查询请求，包含查询文本和参数
        current_user: 当前登录用户
        db (AsyncSession): 数据库会话对象

    Returns:
        APIResponse: 包含查询结果的响应对象
    """
    kb_service = KnowledgeBaseService(db)
    result = await kb_service.query(kb_id, query_request, current_user.id)
    return APIResponse.success(data=result)

@router.get("/{kb_id}/users")
async def list_knowledge_base_users(
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
    result = await kb_service.get_knowledge_base_users(kb_id, current_user.id)
    return APIResponse.success(data=result)

@router.get("/{kb_id}/members")
async def get_knowledge_base_members(
    kb_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取知识库成员列表
    
    Args:
        kb_id: 知识库ID
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        APIResponse: 包含成员列表的响应
    """
    kb_service = KnowledgeBaseService(db)
    result = await kb_service.get_knowledge_base_members(kb_id, current_user.id)
    return APIResponse.success(data=result)

@router.post("/{kb_id}/members")
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
    return APIResponse.success(message="成员添加成功")

@router.put("/{kb_id}/members/{user_id}")
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
    return APIResponse.success(message="成员权限更新成功")

@router.delete("/{kb_id}/members/{user_id}")
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
    return APIResponse.success(message="成员移除成功") 