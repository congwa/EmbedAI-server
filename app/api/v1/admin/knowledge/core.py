"""
知识库核心CRUD操作API
包含创建、更新、删除、获取等基本操作
"""

import time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import get_db
from app.services.auth import get_current_user
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
)
from app.services.knowledge_base import KnowledgeBaseService
from app.core.response_utils import success_response
from app.models.user import User
from app.core.decorators import require_knowledge_base_permission
from app.models.enums import PermissionType
from app.core.logger import Logger

router = APIRouter()


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
    start_time = time.time()
    
    # 记录API请求开始
    Logger.rag_api_request(
        endpoint="/admin/knowledge-bases",
        method="POST",
        user_id=current_user.id,
        params={
            "name": kb.name,
            "domain": kb.domain,
            "has_llm_config": kb.llm_config is not None
        }
    )
    
    try:
        # 记录服务调用开始
        Logger.rag_service_start(
            service="KnowledgeBaseService",
            method="create",
            user_id=current_user.id
        )
        
        kb_service = KnowledgeBaseService(db)
        result = await kb_service.create(kb, current_user.id)
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 记录服务调用成功
        Logger.rag_service_success(
            service="KnowledgeBaseService",
            method="create",
            duration=process_time,
            result_summary={
                "kb_id": result.id,
                "kb_name": result.name,
                "status": result.training_status.value if result.training_status else "unknown"
            }
        )
        
        # 记录API响应成功
        Logger.rag_api_response(
            endpoint="/admin/knowledge-bases",
            method="POST",
            status_code=200,
            process_time=process_time,
            kb_id=result.id,
            result_summary={
                "kb_id": result.id,
                "kb_name": result.name,
                "created": True
            }
        )
        
        return success_response(data=result.to_dict())
        
    except Exception as e:
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 记录服务调用失败
        Logger.rag_service_error(
            service="KnowledgeBaseService",
            method="create",
            error=str(e),
            duration=process_time
        )
        
        # 记录API错误
        Logger.rag_api_error(
            endpoint="/admin/knowledge-bases",
            method="POST",
            error=str(e),
            user_id=current_user.id,
            process_time=process_time
        )
        
        raise


@router.put("/{kb_id}")
@require_knowledge_base_permission(PermissionType.ADMIN)
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
    start_time = time.time()
    
    # 记录API请求开始
    Logger.rag_api_request(
        endpoint=f"/admin/knowledge-bases/{kb_id}",
        method="PUT",
        kb_id=kb_id,
        user_id=current_user.id,
        params={
            "update_fields": list(kb.model_dump(exclude_unset=True).keys())
        }
    )
    
    try:
        # 记录权限检查
        Logger.rag_permission_check(
            kb_id=kb_id,
            user_id=current_user.id,
            required_permission="ADMIN",
            granted=True
        )
        
        kb_service = KnowledgeBaseService(db)
        result = await kb_service.update(kb_id, kb, current_user.id)
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 记录API响应成功
        Logger.rag_api_response(
            endpoint=f"/admin/knowledge-bases/{kb_id}",
            method="PUT",
            status_code=200,
            process_time=process_time,
            kb_id=kb_id,
            result_summary={
                "updated": True,
                "kb_name": result.name if hasattr(result, 'name') else "unknown"
            }
        )
        
        return success_response(data=result.to_dict())
        
    except Exception as e:
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 记录API错误
        Logger.rag_api_error(
            endpoint=f"/admin/knowledge-bases/{kb_id}",
            method="PUT",
            error=str(e),
            kb_id=kb_id,
            user_id=current_user.id,
            process_time=process_time
        )
        
        raise


@router.delete(
    "/{kb_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除知识库",
    description="软删除指定的知识库，只有所有者才能执行此操作。",
)
async def delete_knowledge_base(
    kb_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """软删除知识库接口"""
    kb_service = KnowledgeBaseService(db)
    await kb_service.delete(kb_id, current_user.id)
    return


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
    return success_response(data=result)


@router.get("/{kb_id}")
@require_knowledge_base_permission(PermissionType.VIEWER)
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
    start_time = time.time()
    
    # 记录API请求开始
    Logger.rag_api_request(
        endpoint=f"/admin/knowledge-bases/{kb_id}",
        method="GET",
        kb_id=kb_id,
        user_id=current_user.id
    )
    
    try:
        # 记录权限检查
        Logger.rag_permission_check(
            kb_id=kb_id,
            user_id=current_user.id,
            required_permission="VIEWER",
            granted=True
        )
        
        kb_service = KnowledgeBaseService(db)
        result = await kb_service.get(kb_id, current_user.id)
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 记录API响应成功
        Logger.rag_api_response(
            endpoint=f"/admin/knowledge-bases/{kb_id}",
            method="GET",
            status_code=200,
            process_time=process_time,
            kb_id=kb_id,
            result_summary={
                "kb_name": result.name if hasattr(result, 'name') else "unknown",
                "training_status": result.training_status.value if hasattr(result, 'training_status') and result.training_status else "unknown",
                "member_count": len(result.members) if hasattr(result, 'members') and result.members else 0
            }
        )
        
        return success_response(data=result.to_dict())
        
    except Exception as e:
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 记录API错误
        Logger.rag_api_error(
            endpoint=f"/admin/knowledge-bases/{kb_id}",
            method="GET",
            error=str(e),
            kb_id=kb_id,
            user_id=current_user.id,
            process_time=process_time
        )
        
        raise 