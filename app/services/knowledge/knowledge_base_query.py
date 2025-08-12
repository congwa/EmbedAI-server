"""
知识库查询服务
负责RAG查询、查询权限检查和查询结果处理
"""
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from fastapi import HTTPException, status

from app.models.knowledge_base import KnowledgeBase, TrainingStatus
from app.schemas.identity import UserContext
from app.rag.retrieval.retrieval_service import RetrievalService
from app.rag.retrieval.retrieval_methods import RetrievalMethod
from app.rag.rerank.rerank_type import RerankMode
from app.services.audit import AuditManager
from app.core.logger import Logger


class KnowledgeBaseQueryService:
    """知识库查询服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.retrieval_service = RetrievalService(db)
        self.audit_manager = AuditManager(db)

    async def query_rag(
        self,
        kb_id: int,
        user_context: UserContext,
        query: str,
        method: str = RetrievalMethod.SEMANTIC_SEARCH,
        top_k: int = 5,
        use_rerank: bool = False,
        rerank_mode: str = RerankMode.WEIGHTED_SCORE,
        skip_permission_check: bool = False,
    ) -> dict:
        """RAG查询知识库

        Args:
            kb_id: 知识库ID
            user_context: 用户上下文信息
            query: 查询内容
            method: 检索方法
            top_k: 返回结果数量
            use_rerank: 是否使用重排序
            rerank_mode: 重排序模式
            skip_permission_check: 是否跳过权限检查

        Returns:
            dict: 查询结果

        Raises:
            HTTPException: 当权限不足或知识库不存在时
        """
        import time

        start_time = time.time()

        # 记录服务调用开始
        Logger.rag_service_start(
            service="KnowledgeBaseQueryService",
            method="query_rag",
            kb_id=kb_id,
            user_id=user_context.user_id,
        )

        # 记录查询开始
        Logger.rag_query_start(
            kb_id=kb_id,
            query=query,
            method=method,
            params={
                "top_k": top_k,
                "use_rerank": use_rerank,
                "rerank_mode": rerank_mode,
                "skip_permission_check": skip_permission_check,
            },
            user_id=user_context.user_id,
        )

        try:
            Logger.info(
                f"处理知识库 {kb_id} 的RAG查询请求，"
                f"来自 {user_context.user_type} 用户 {user_context.user_id}"
            )

            # 检查权限（仅当 skip_permission_check 为 False 时）
            if not skip_permission_check:
                from app.services.knowledge.knowledge_base_core import KnowledgeBaseCoreService
                core_service = KnowledgeBaseCoreService(self.db)
                from app.models.knowledge_base import PermissionType
                
                has_permission = await core_service.check_kb_permission(
                    kb_id=kb_id,
                    identity_id=user_context.identity_id,
                    required_permission=PermissionType.VIEWER,
                )

                # 记录权限检查结果
                Logger.rag_permission_check(
                    kb_id=kb_id,
                    user_id=user_context.user_id,
                    required_permission="VIEWER",
                    granted=has_permission,
                )

                if not has_permission:
                    Logger.warning(
                        f"查询被拒绝: {user_context.user_type} 用户 {user_context.user_id} "
                        f"没有权限查询知识库 {kb_id}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="没有足够的权限执行此操作",
                    )
            else:
                # 记录跳过权限检查
                Logger.rag_permission_check(
                    kb_id=kb_id,
                    user_id=user_context.user_id,
                    required_permission="VIEWER",
                    granted=True,
                    skipped=True,
                )

            # 获取知识库
            kb = (
                await self.db.execute(
                    select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
                )
            ).scalar_one_or_none()

            if not kb:
                Logger.error(f"查询失败: 知识库 {kb_id} 不存在")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在"
                )

            if kb.training_status != TrainingStatus.TRAINED:
                Logger.warning(
                    f"查询被拒绝: 知识库 {kb_id} 尚未训练完成 "
                    f"(状态: {kb.training_status})"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="知识库尚未训练完成"
                )

            # 创建LLM配置
            llm_config = kb.llm_config
            if isinstance(llm_config, dict):
                from app.schemas.llm import LLMConfig

                llm_config = LLMConfig.model_validate(llm_config)

            # 执行RAG查询
            Logger.debug(f"开始执行RAG查询: 知识库ID {kb_id}, 方法: {method}")

            results = await self.retrieval_service.query(
                knowledge_base=kb,
                query=query,
                llm_config=llm_config,
                method=method,
                top_k=top_k,
                use_rerank=use_rerank,
                rerank_mode=rerank_mode,
                user_id=str(user_context.user_id),
            )

            # 提取结果统计信息
            result_count = len(results) if results else 0
            scores = []
            if results:
                for result in results:
                    if isinstance(result, dict) and "score" in result:
                        scores.append(result["score"])
                    elif hasattr(result, "metadata") and isinstance(
                        result.metadata, dict
                    ):
                        scores.append(result.metadata.get("score", 0.0))

            # 记录检索结果
            Logger.rag_retrieval_result(
                kb_id=kb_id,
                query=query,
                result_count=result_count,
                scores=scores,
                method=method,
            )

            Logger.info(f"知识库 {kb_id} 查询成功: '{query[:100]}...' (如果更长)")

            # 构建元数据
            doc_metadata = {
                "kb_id": kb_id,
                "top_k": top_k,
                "method": method,
                "use_rerank": use_rerank,
                "rerank_mode": rerank_mode if use_rerank else None,
                "user_type": user_context.user_type,
                "user_id": user_context.user_id,
            }

            # 计算处理时间
            process_time = time.time() - start_time

            # 记录查询完成
            Logger.rag_query_complete(
                kb_id=kb_id,
                query=query,
                success=True,
                duration=process_time,
                result_count=result_count,
            )

            # 记录服务调用成功
            Logger.rag_service_success(
                service="KnowledgeBaseQueryService",
                method="query_rag",
                duration=process_time,
                result_summary={
                    "result_count": result_count,
                    "avg_score": sum(scores) / len(scores) if scores else 0.0,
                    "method": method,
                    "use_rerank": use_rerank,
                },
            )

            # 记录审计日志
            await self.audit_manager.log_query(
                user_context=user_context,
                kb_id=kb_id,
                query=query,
                status="success",
                method=method,
                use_rerank=use_rerank,
                rerank_mode=rerank_mode if use_rerank else None,
                top_k=top_k,
                result_count=len(results),
            )

            return {"query": query, "results": results, "doc_metadata": doc_metadata}

        except HTTPException:
            # 计算处理时间
            process_time = time.time() - start_time

            # 记录查询失败
            Logger.rag_query_complete(
                kb_id=kb_id,
                query=query,
                success=False,
                duration=process_time,
                result_count=0,
            )

            # 记录服务调用失败（HTTP异常）
            Logger.rag_service_error(
                service="KnowledgeBaseQueryService",
                method="query_rag",
                error="HTTP异常",
                duration=process_time,
            )

            # 直接抛出 HTTP 异常，因为这些是预期的错误
            raise
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time

            import traceback

            error_info = traceback.format_exc()
            Logger.error(
                f"知识库 {kb_id} 查询失败\n"
                f"错误: {str(e)}\n"
                f"堆栈跟踪:\n{error_info}"
            )

            # 记录查询失败
            Logger.rag_query_complete(
                kb_id=kb_id,
                query=query,
                success=False,
                duration=process_time,
                result_count=0,
            )

            # 记录服务调用失败
            Logger.rag_service_error(
                service="KnowledgeBaseQueryService",
                method="query_rag",
                error=str(e),
                duration=process_time,
            )

            # 记录错误审计
            await self.audit_manager.log_query(
                user_context=user_context,
                kb_id=kb_id,
                query=query,
                status="error",
                method=method,
                use_rerank=use_rerank,
                rerank_mode=rerank_mode if use_rerank else None,
                top_k=top_k,
                error=f"{str(e)}\n{error_info}",
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"查询执行失败: {str(e)}",
            )

    async def query(
        self,
        kb_id: int,
        user_context: UserContext,
        query: str,
        top_k: int = 5,
        method: str = RetrievalMethod.HYBRID_SEARCH,
        use_rerank: bool = True,
        rerank_mode: str = RerankMode.WEIGHTED_SCORE,
        skip_permission_check: bool = False,
    ) -> dict:
        """查询知识库

        Args:
            kb_id: 知识库ID
            user_context: 用户上下文信息
            query: 查询内容
            top_k: 返回结果数量
            method: 检索方法
            use_rerank: 是否使用重排序
            rerank_mode: 重排序模式
            skip_permission_check: 是否跳过权限检查

        Returns:
            dict: 查询结果

        Raises:
            HTTPException: 当权限不足或知识库不存在时
        """
        # 使用RAG查询替代原有查询
        return await self.query_rag(
            kb_id=kb_id,
            user_context=user_context,
            query=query,
            method=method,
            top_k=top_k,
            use_rerank=use_rerank,
            rerank_mode=rerank_mode,
            skip_permission_check=skip_permission_check,
        ) 