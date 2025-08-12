"""
知识库训练相关API
包含训练、队列管理等操作
"""

import time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import get_db
from app.services.auth import get_current_user
from app.services.knowledge_base import KnowledgeBaseService
from app.core.response_utils import success_response
from app.models.user import User
from app.core.decorators import require_knowledge_base_permission
from app.models.enums import PermissionType
from app.core.logger import Logger

router = APIRouter()


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
        
        return success_response(data=result.to_dict())
        
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


@router.get("/training-queue/status")
async def get_training_queue_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取训练队列状态

    Args:
        current_user: 当前登录用户
        db (AsyncSession): 数据库会话对象

    Returns:
        APIResponse: 包含训练队列状态的响应对象
    """
    try:
        kb_service = KnowledgeBaseService(db)
        result = await kb_service.get_training_queue_status(current_user.id)
        return success_response(data=result)
        
    except Exception as e:
        Logger.error(f"获取训练队列状态失败: {str(e)}")
        raise 