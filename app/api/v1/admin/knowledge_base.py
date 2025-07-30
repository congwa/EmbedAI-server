import time
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
from app.core.decorators import require_knowledge_base_permission
from app.models.enums import PermissionType
from app.core.logger import Logger

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
        
        return APIResponse.success(data=result.to_dict())
        
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
        
        return APIResponse.success(data=result.to_dict())
        
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
    current_user: CurrentUser,
    knowledge_base_service: KnowledgeBaseService = Depends(get_knowledge_base_service),
):
    """软删除知识库接口"""
    await knowledge_base_service.delete(kb_id, current_user.id)
    return


@router.post("/{kb_id}/train")
@require_knowledge_base_permission(PermissionType.EDITOR)
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
    start_time = time.time()
    
    # 初始化RAG训练追踪
    trace_id = Logger.init_rag_trace(
        kb_id=kb_id,
        user_id=current_user.id,
        operation_type="training"
    )
    
    # 记录API请求开始
    Logger.rag_api_request(
        endpoint=f"/admin/knowledge-bases/{kb_id}/train",
        method="POST",
        kb_id=kb_id,
        user_id=current_user.id,
        params={"trace_id": trace_id}
    )
    
    try:
        # 记录权限检查
        Logger.rag_permission_check(
            kb_id=kb_id,
            user_id=current_user.id,
            required_permission="EDITOR",
            granted=True
        )
        
        # 记录服务调用开始
        Logger.rag_service_start(
            service="KnowledgeBaseService",
            method="train",
            kb_id=kb_id,
            user_id=current_user.id
        )
        
        kb_service = KnowledgeBaseService(db)
        result = await kb_service.train(kb_id, current_user.id)
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 记录服务调用成功
        Logger.rag_service_success(
            service="KnowledgeBaseService",
            method="train",
            duration=process_time,
            result_summary={
                "kb_id": kb_id,
                "training_status": result.training_status.value if result.training_status else "unknown",
                "training_started": result.training_started_at is not None
            }
        )
        
        # 记录训练开始（如果成功启动）
        if hasattr(result, 'training_status') and result.training_status:
            if result.training_status.value in ['TRAINING', 'QUEUED']:
                Logger.rag_training_start(
                    kb_id=kb_id,
                    document_count=0,  # 这里可以从服务中获取实际文档数量
                    config={
                        "llm_config": result.llm_config if hasattr(result, 'llm_config') else {},
                        "trace_id": trace_id
                    }
                )
        
        # 记录API响应成功
        Logger.rag_api_response(
            endpoint=f"/admin/knowledge-bases/{kb_id}/train",
            method="POST",
            status_code=200,
            process_time=process_time,
            kb_id=kb_id,
            result_summary={
                "training_status": result.training_status.value if result.training_status else "unknown",
                "training_initiated": True
            }
        )
        
        return APIResponse.success(data=result.to_dict())
        
    except Exception as e:
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 记录服务调用失败
        Logger.rag_service_error(
            service="KnowledgeBaseService",
            method="train",
            error=str(e),
            duration=process_time
        )
        
        # 记录API错误
        Logger.rag_api_error(
            endpoint=f"/admin/knowledge-bases/{kb_id}/train",
            method="POST",
            error=str(e),
            kb_id=kb_id,
            user_id=current_user.id,
            process_time=process_time
        )
        
        raise

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
        
        return APIResponse.success(data=result.to_dict())
        
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

@router.post("/{kb_id}/query")
@require_knowledge_base_permission(PermissionType.VIEWER)
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
    start_time = time.time()
    
    # 提取查询参数
    query_text = query_request.get('query', '')
    method = query_request.get('method', 'hybrid_search')
    top_k = query_request.get('top_k', 5)
    use_rerank = query_request.get('use_rerank', False)
    
    # 初始化RAG查询追踪
    trace_id = Logger.init_rag_trace(
        kb_id=kb_id,
        user_id=current_user.id,
        operation_type="query"
    )
    
    # 记录API请求开始
    Logger.rag_api_request(
        endpoint=f"/admin/knowledge-bases/{kb_id}/query",
        method="POST",
        kb_id=kb_id,
        user_id=current_user.id,
        params={
            "query_length": len(query_text),
            "method": method,
            "top_k": top_k,
            "use_rerank": use_rerank,
            "trace_id": trace_id
        }
    )
    
    # 记录查询开始
    Logger.rag_query_start(
        kb_id=kb_id,
        query=query_text,
        method=method,
        params={
            "top_k": top_k,
            "use_rerank": use_rerank
        },
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
        
        # 记录服务调用开始
        Logger.rag_service_start(
            service="KnowledgeBaseService",
            method="query",
            kb_id=kb_id,
            user_id=current_user.id
        )
        
        kb_service = KnowledgeBaseService(db)
        result = await kb_service.query(kb_id, query_request, current_user.id)
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 提取结果信息
        result_count = 0
        scores = []
        if isinstance(result, dict) and 'results' in result:
            results_list = result['results']
            result_count = len(results_list)
            scores = [r.get('score', 0.0) for r in results_list if isinstance(r, dict)]
        
        # 记录检索结果
        Logger.rag_retrieval_result(
            kb_id=kb_id,
            query=query_text,
            result_count=result_count,
            scores=scores,
            method=method
        )
        
        # 记录查询完成
        Logger.rag_query_complete(
            kb_id=kb_id,
            query=query_text,
            success=True,
            duration=process_time,
            result_count=result_count
        )
        
        # 记录服务调用成功
        Logger.rag_service_success(
            service="KnowledgeBaseService",
            method="query",
            duration=process_time,
            result_summary={
                "result_count": result_count,
                "avg_score": sum(scores) / len(scores) if scores else 0.0,
                "method": method
            }
        )
        
        # 记录API响应成功
        Logger.rag_api_response(
            endpoint=f"/admin/knowledge-bases/{kb_id}/query",
            method="POST",
            status_code=200,
            process_time=process_time,
            kb_id=kb_id,
            result_summary={
                "result_count": result_count,
                "query_success": True,
                "method": method
            }
        )
        
        return APIResponse.success(data=result)
        
    except Exception as e:
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 记录查询失败
        Logger.rag_query_complete(
            kb_id=kb_id,
            query=query_text,
            success=False,
            duration=process_time,
            result_count=0
        )
        
        # 记录服务调用失败
        Logger.rag_service_error(
            service="KnowledgeBaseService",
            method="query",
            error=str(e),
            duration=process_time
        )
        
        # 记录API错误
        Logger.rag_api_error(
            endpoint=f"/admin/knowledge-bases/{kb_id}/query",
            method="POST",
            error=str(e),
            kb_id=kb_id,
            user_id=current_user.id,
            process_time=process_time
        )
        
        raise

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
    return APIResponse.success(data=result)

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
    return APIResponse.success(message="成员添加成功")

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
    return APIResponse.success(message="成员权限更新成功")

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
    return APIResponse.success(message="成员移除成功") 