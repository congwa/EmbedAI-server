from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
import json

from app.core.redis_manager import redis_manager
from app.core.logger import Logger
from app.schemas.identity import UserContext

class AuditManager:
    """审计管理器，用于记录和管理操作日志"""
    
    def __init__(self, db: Session):
        self.db = db
        
    async def log_query(
        self,
        user_context: UserContext,
        kb_id: int,
        query: str,
        status: str,
        method: Optional[str] = None,
        use_rerank: Optional[bool] = None,
        rerank_mode: Optional[str] = None,
        top_k: Optional[int] = None,
        result_count: Optional[int] = None,
        error: Optional[str] = None
    ) -> None:
        """记录查询操作日志"""
        audit_log = {
            "timestamp": datetime.now().isoformat(),
            "operation": "knowledge_base_query",
            "user_type": user_context.user_type,
            "user_id": user_context.user_id,
            "identity_id": user_context.identity_id,
            "client_id": user_context.client_id,
            "resource": {
                "type": "knowledge_base",
                "id": kb_id
            },
            "details": {
                "query": query[:200],  # 限制查询内容长度
                "status": status
            }
        }
        
        # 添加RAG相关信息
        if method:
            audit_log["details"]["method"] = method
        if use_rerank is not None:
            audit_log["details"]["use_rerank"] = use_rerank
        if rerank_mode:
            audit_log["details"]["rerank_mode"] = rerank_mode
        if top_k:
            audit_log["details"]["top_k"] = top_k
        if result_count is not None:
            audit_log["details"]["result_count"] = result_count
        if error:
            audit_log["details"]["error"] = error
            
        # 保存到Redis用于实时监控
        await redis_manager.lpush(
            "audit_logs",
            json.dumps(audit_log),
            expire=timedelta(days=7)
        )
        
        # TODO: 异步保存到持久化存储
        Logger.info(f"Audit log created for query operation: {audit_log}")
        
    async def log_operation(
        self,
        user_context: UserContext,
        operation: str,
        resource_type: str,
        resource_id: int,
        status: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """记录一般操作日志"""
        audit_log = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "user_type": user_context.user_type,
            "user_id": user_context.user_id,
            "identity_id": user_context.identity_id,
            "client_id": user_context.client_id,
            "resource": {
                "type": resource_type,
                "id": resource_id
            },
            "details": details or {},
            "status": status
        }
        
        # 保存到Redis用于实时监控
        await redis_manager.lpush(
            "audit_logs",
            json.dumps(audit_log),
            expire=timedelta(days=7)
        )
        
        # TODO: 异步保存到持久化存储
        Logger.info(f"Audit log created for {operation}: {audit_log}")
        
    async def log_training(
        self,
        user_context: UserContext,
        kb_id: int,
        status: str,
        document_count: Optional[int] = None,
        chunk_count: Optional[int] = None,
        embedding_count: Optional[int] = None,
        duration: Optional[float] = None,
        error: Optional[str] = None
    ) -> None:
        """记录训练操作日志"""
        details = {
            "status": status
        }
        
        if document_count is not None:
            details["document_count"] = document_count
        if chunk_count is not None:
            details["chunk_count"] = chunk_count
        if embedding_count is not None:
            details["embedding_count"] = embedding_count
        if duration is not None:
            details["duration_seconds"] = duration
        if error:
            details["error"] = error
            
        await self.log_operation(
            user_context=user_context,
            operation="knowledge_base_training",
            resource_type="knowledge_base",
            resource_id=kb_id,
            status=status,
            details=details
        )
    
    async def get_user_operations(
        self,
        user_context: UserContext,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        operation_type: Optional[str] = None
    ) -> List[Dict]:
        """获取用户操作历史"""
        # TODO: 实现从持久化存储查询历史记录
        pass 