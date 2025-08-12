"""
知识库查询相关API
包含RAG查询、权限检查等操作
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
        
        return success_response(data=result)
        
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