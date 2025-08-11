from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any, Sequence
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException, status
from app.models.knowledge_base import (
    KnowledgeBase,
    TrainingStatus,
    knowledge_base_users,
    PermissionType,
)
from app.models.document import Document
from app.models.user import User
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBasePermissionCreate,
    KnowledgeBasePermissionUpdate,
    KnowledgeBaseMemberList,
    KnowledgeBaseMemberInfo,
    KnowledgeBaseMemberCreate,
    KnowledgeBaseMemberUpdate,
)
from app.utils.session import SessionManager
from app.utils.rate_limit import rate_limit
from app.core.config import settings
from sqlalchemy.sql import select
from app.core.logger import Logger
from app.schemas.identity import UserContext, UserType
from app.models.identity import UserIdentity
from app.rag.training.training_manager import RAGTrainingManager
from app.rag.retrieval.retrieval_service import RetrievalService
from app.rag.retrieval.retrieval_methods import RetrievalMethod
from app.rag.rerank.rerank_type import RerankMode
from app.services.audit import AuditManager
from app.utils.tasks import train_knowledge_base
from app.services.prompt import PromptService
from app.services.prompt_analytics import PromptAnalyticsService


class KnowledgeBaseService:
    def __init__(self, db: Session):
        self.db = db
        self.session_manager = SessionManager(db)
        self.retrieval_service = RetrievalService(db)
        self.audit_manager = AuditManager(db)

    async def check_permission(
        self, kb_id: int, user_id: int, required_permission: PermissionType
    ) -> bool:
        """检查用户对知识库的权限"""
        kb = (
            await self.db.execute(
                select(KnowledgeBase).filter(
                    and_(KnowledgeBase.id == kb_id, KnowledgeBase.is_deleted == False)
                )
            )
        ).scalar_one_or_none()

        if not kb:
            return False

        return await kb.check_permission(self.db, user_id, required_permission)

    async def get_user_permission(
        self, kb_id: int, user_id: int
    ) -> Optional[PermissionType]:
        """获取用户对知识库的权限级别"""
        kb = (
            await self.db.execute(
                select(KnowledgeBase).filter(
                    and_(KnowledgeBase.id == kb_id, KnowledgeBase.is_deleted == False)
                )
            )
        ).scalar_one_or_none()

        if not kb:
            return None

        return await kb.get_member_permission(self.db, user_id)

    async def create(self, kb: KnowledgeBaseCreate, owner_id: int) -> KnowledgeBase:
        """创建新知识库"""
        import time

        start_time = time.time()

        # 记录服务调用开始
        Logger.rag_service_start(
            service="KnowledgeBaseService", method="create", user_id=owner_id
        )

        Logger.info(f"Creating new knowledge base '{kb.name}' for owner {owner_id}")

        # 使用默认配置
        llm_config = settings.DEFAULT_LLM_CONFIG
        if kb.llm_config:
            # 合并用户配置
            if "llm" in kb.llm_config.model_dump():
                llm_config.llm = kb.llm_config.llm
            if "embeddings" in kb.llm_config.model_dump():
                llm_config.embeddings = kb.llm_config.embeddings
            Logger.debug(f"Custom LLM config provided for knowledge base '{kb.name}'")

        # 生成工作目录路径
        working_dir = (
            f"workspaces/kb_{owner_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        db_kb = KnowledgeBase(
            name=kb.name,
            owner_id=owner_id,
            domain=kb.domain,
            example_queries=kb.example_queries or [],
            entity_types=kb.entity_types or [],
            llm_config=llm_config.model_dump(),
            training_status=TrainingStatus.INIT,
            working_dir=working_dir,
        )

        self.db.add(db_kb)
        await self.db.commit()
        await self.db.refresh(db_kb)

        # 添加所有者权限
        await self.db.execute(
            knowledge_base_users.insert().values(
                knowledge_base_id=db_kb.id,
                user_id=owner_id,
                permission=PermissionType.OWNER,
                created_at=datetime.now(),
            )
        )

        await self.db.commit()
        await self.db.refresh(db_kb)

        # 计算处理时间
        process_time = time.time() - start_time

        # 记录服务调用成功
        Logger.rag_service_success(
            service="KnowledgeBaseService",
            method="create",
            duration=process_time,
            result_summary={
                "kb_id": db_kb.id,
                "kb_name": db_kb.name,
                "owner_id": owner_id,
                "training_status": (
                    db_kb.training_status.value if db_kb.training_status else "unknown"
                ),
                "working_dir": working_dir,
            },
        )

        Logger.info(
            f"Knowledge base '{kb.name}' (ID: {db_kb.id}) created successfully with working directory: {working_dir}"
        )
        return db_kb

    async def train(self, kb_id: int, user_id: int) -> KnowledgeBase:
        """训练知识库"""
        import time

        start_time = time.time()

        # 记录服务调用开始
        Logger.rag_service_start(
            service="KnowledgeBaseService", method="train", kb_id=kb_id, user_id=user_id
        )

        Logger.info(f"开始训练知识库 {kb_id}，请求用户: {user_id}")

        # 创建用户上下文
        user_context = UserContext(
            user_type=UserType.OFFICIAL,
            user_id=user_id,
            identity_id=None,
            client_id=None,
        )

        try:
            # 检查权限
            permission_granted = await self.check_permission(
                kb_id, user_id, PermissionType.EDITOR
            )

            # 记录权限检查结果
            Logger.rag_permission_check(
                kb_id=kb_id,
                user_id=user_id,
                required_permission="EDITOR",
                granted=permission_granted,
            )

            if not permission_granted:
                Logger.warning(f"训练被拒绝: 用户 {user_id} 没有权限训练知识库 {kb_id}")

                # 记录审计日志
                await self.audit_manager.log_training(
                    user_context=user_context,
                    kb_id=kb_id,
                    status="permission_denied",
                    error="用户没有足够的权限执行此操作",
                )

                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="没有足够的权限执行此操作",
                )

            kb = (
                await self.db.execute(
                    select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
                )
            ).scalar_one_or_none()

            if not kb:
                Logger.error(f"训练失败: 知识库 {kb_id} 不存在")

                # 记录审计日志
                await self.audit_manager.log_training(
                    user_context=user_context,
                    kb_id=kb_id,
                    status="not_found",
                    error="知识库不存在",
                )

                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在"
                )

            # 检查知识库当前状态是否允许训练
            if not kb.can_train:
                Logger.warning(
                    f"训练被拒绝: 知识库 {kb_id} 状态为 {kb.training_status}"
                )

                # 记录审计日志
                await self.audit_manager.log_training(
                    user_context=user_context,
                    kb_id=kb_id,
                    status="invalid_status",
                    error=f"当前状态({kb.training_status})不允许训练",
                )

                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"当前状态({kb.training_status})不允许训练，只有初始状态或训练失败的知识库可以训练",
                )

            # 检查是否已经在队列中
            if kb.training_status == TrainingStatus.QUEUED:
                Logger.warning(f"训练被拒绝: 知识库 {kb_id} 已经在队列中")

                # 记录审计日志
                await self.audit_manager.log_training(
                    user_context=user_context,
                    kb_id=kb_id,
                    status="already_queued",
                    error="知识库已在训练队列中",
                )

                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="知识库已在训练队列中",
                )

            # 获取知识库的所有未删除文档
            documents = (
                (
                    await self.db.execute(
                        select(Document).filter(
                            Document.knowledge_base_id == kb_id,
                            Document.is_deleted == False,
                        )
                    )
                )
                .scalars()
                .all()
            )

            if not documents:
                Logger.error(f"训练失败: 知识库 {kb_id} 没有可用文档")

                # 记录审计日志
                await self.audit_manager.log_training(
                    user_context=user_context,
                    kb_id=kb_id,
                    status="no_documents",
                    error="没有可用于训练的文档",
                )

                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="没有可用于训练的文档",
                )

            Logger.info(f"找到 {len(documents)} 个文档用于训练知识库 {kb_id}")

            # 记录文档统计信息
            doc_types = {}
            total_size = 0
            for doc in documents:
                doc_type = doc.file_type or "unknown"
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
                if hasattr(doc, "file_size") and doc.file_size:
                    total_size += doc.file_size

            Logger.rag_document_processing_start(
                kb_id=kb_id,
                document_count=len(documents),
                config={
                    "document_types": doc_types,
                    "total_size_mb": total_size / 1024 / 1024 if total_size > 0 else 0,
                    "llm_config": kb.llm_config if hasattr(kb, "llm_config") else {},
                },
            )

            # 创建训练管理器
            training_manager = RAGTrainingManager(self.db)

            # 检查是否启用训练队列
            if getattr(settings, "ENABLE_TRAINING_QUEUE", False):
                # 检查是否有其他知识库正在训练
                training_kb = (
                    await self.db.execute(
                        select(KnowledgeBase).filter(
                            KnowledgeBase.training_status == TrainingStatus.TRAINING
                        )
                    )
                ).scalar_one_or_none()

                if training_kb:
                    # 如果有其他知识库在训练，将当前知识库添加到队列
                    Logger.info(f"另一个知识库正在训练，将知识库 {kb_id} 加入队列")
                    await training_manager.update_training_status(
                        kb_id, TrainingStatus.QUEUED
                    )

                    # 记录审计日志
                    await self.audit_manager.log_training(
                        user_context=user_context,
                        kb_id=kb_id,
                        status="queued",
                        document_count=len(documents),
                    )

                    await self.db.refresh(kb)
                    return kb

            # 如果没有其他知识库在训练，直接开始训练
            Logger.info(f"开始立即训练知识库 {kb_id}")
            await training_manager.update_training_status(
                kb_id, TrainingStatus.TRAINING
            )

            # 记录审计日志
            await self.audit_manager.log_training(
                user_context=user_context,
                kb_id=kb_id,
                status="started",
                document_count=len(documents),
            )

            # 记录训练开始
            Logger.rag_training_start(
                kb_id=kb_id,
                document_count=len(documents),
                config={
                    "llm_config": kb.llm_config if hasattr(kb, "llm_config") else {},
                    "working_dir": kb.working_dir if hasattr(kb, "working_dir") else "",
                    "training_mode": "immediate",
                },
            )

            # 启动异步训练任务
            train_knowledge_base(kb_id)

            await self.db.refresh(kb)

            # 计算处理时间
            process_time = time.time() - start_time

            # 记录服务调用成功
            Logger.rag_service_success(
                service="KnowledgeBaseService",
                method="train",
                duration=process_time,
                result_summary={
                    "kb_id": kb_id,
                    "training_status": (
                        kb.training_status.value if kb.training_status else "unknown"
                    ),
                    "document_count": len(documents),
                    "training_initiated": True,
                },
            )

            return kb

        except HTTPException:
            # 计算处理时间
            process_time = time.time() - start_time

            # 记录服务调用失败（HTTP异常）
            Logger.rag_service_error(
                service="KnowledgeBaseService",
                method="train",
                error="HTTP异常",
                duration=process_time,
            )

            # 直接抛出HTTP异常
            raise
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time

            Logger.error(f"训练知识库 {kb_id} 时发生意外错误: {str(e)}")

            # 记录服务调用失败
            Logger.rag_service_error(
                service="KnowledgeBaseService",
                method="train",
                error=str(e),
                duration=process_time,
            )

            # 记录审计日志
            await self.audit_manager.log_training(
                user_context=user_context, kb_id=kb_id, status="error", error=str(e)
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"训练知识库失败: {str(e)}",
            )

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
            service="KnowledgeBaseService",
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
                has_permission = await self.check_kb_permission(
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
                service="KnowledgeBaseService",
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
                service="KnowledgeBaseService",
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
                service="KnowledgeBaseService",
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

    async def delete(self, kb_id: int, user_id: int) -> None:
        """软删除知识库"""
        Logger.info(f"Attempting to delete knowledge base {kb_id} by user {user_id}")

        # 检查权限，只有所有者可以删除
        permission_granted = await self.check_permission(
            kb_id, user_id, PermissionType.OWNER
        )
        if not permission_granted:
            Logger.warning(f"Delete rejected: User {user_id} is not the owner of KB {kb_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有知识库所有者才能删除"
            )

        kb = await self.get(kb_id, user_id)
        if not kb:
            # get方法已经处理了不存在的情况，这里为了逻辑完备
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在"
            )

        kb.is_deleted = True
        kb.deleted_at = datetime.now()
        self.db.add(kb)
        await self.db.commit()
        Logger.info(f"Knowledge base {kb_id} has been soft-deleted.")

    async def get(self, kb_id: int, user_id: int) -> KnowledgeBase:
        """获取知识库详情"""
        if not await self.check_permission(kb_id, user_id, PermissionType.VIEWER):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="没有足够的权限执行此操作"
            )

        kb = (
            await self.db.execute(
                select(KnowledgeBase).filter(
                    and_(KnowledgeBase.id == kb_id, KnowledgeBase.is_deleted == False)
                )
            )
        ).scalar_one_or_none()

        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在"
            )

        # 获取知识库成员
        kb.members = await kb.get_all_members(self.db)

        return kb

    async def update(
        self, kb_id: int, kb: KnowledgeBaseUpdate, user_id: int
    ) -> KnowledgeBase:
        """更新知识库"""
        if not await self.check_permission(kb_id, user_id, PermissionType.EDITOR):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="没有足够的权限执行此操作"
            )

        db_kb = (
            await self.db.execute(
                select(KnowledgeBase).filter(
                    and_(KnowledgeBase.id == kb_id, KnowledgeBase.is_deleted == False)
                )
            )
        ).scalar_one_or_none()

        if not db_kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在"
            )

        for field, value in kb.model_dump(exclude_unset=True).items():
            setattr(db_kb, field, value)

        await self.db.commit()
        await self.db.refresh(db_kb)
        return db_kb

    async def add_user(
        self,
        kb_id: int,
        permission_data: KnowledgeBasePermissionCreate,
        current_user_id: int,
    ) -> None:
        """添加用户到知识库"""
        if not await self.check_permission(
            kb_id, current_user_id, PermissionType.ADMIN
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="没有足够的权限执行此操作"
            )

        # 检查用户是否已有权限
        existing_permission = await self.get_user_permission(
            kb_id, permission_data.user_id
        )
        if existing_permission:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户已经拥有此知识库的权限",
            )

        await self.db.execute(
            knowledge_base_users.insert().values(
                knowledge_base_id=kb_id,
                user_id=permission_data.user_id,
                permission=permission_data.permission,
            )
        )
        await self.db.commit()

    async def update_user_permission(
        self,
        kb_id: int,
        user_id: int,
        permission_data: KnowledgeBasePermissionUpdate,
        current_user_id: int,
    ) -> None:
        """更新用户的知识库权限"""
        if not await self.check_permission(
            kb_id, current_user_id, PermissionType.ADMIN
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="没有足够的权限执行此操作"
            )

        # 不能修改所有者的权限
        kb = (
            await self.db.execute(
                select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
            )
        ).scalar_one_or_none()

        if kb.owner_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能修改知识库所有者的权限",
            )

        await self.db.execute(
            knowledge_base_users.update()
            .where(
                and_(
                    knowledge_base_users.c.knowledge_base_id == kb_id,
                    knowledge_base_users.c.user_id == user_id,
                )
            )
            .values(permission=permission_data.permission)
        )
        await self.db.commit()

    async def remove_user(self, kb_id: int, user_id: int, current_user_id: int) -> None:
        """从知识库中移除用户"""
        if not await self.check_permission(
            kb_id, current_user_id, PermissionType.ADMIN
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="没有足够的权限执行此操作"
            )

        # 不能移除所有者
        kb = (
            await self.db.execute(
                select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
            )
        ).scalar_one_or_none()

        if kb.owner_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="不能移除知识库所有者"
            )

        await self.db.execute(
            knowledge_base_users.delete().where(
                and_(
                    knowledge_base_users.c.knowledge_base_id == kb_id,
                    knowledge_base_users.c.user_id == user_id,
                )
            )
        )
        await self.db.commit()

    async def get_user_knowledge_bases(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户可访问的所有知识库，并包含成员信息

        Args:
            user_id (int): 用户ID

        Returns:
            List[Dict[str, Any]]: 知识库列表，每个知识库包含成员信息
        """
        user: User = (
            await self.db.execute(select(User).filter(User.id == user_id))
        ).scalar_one_or_none()

        # 获取知识库列表
        if user.is_admin:
            knowledge_bases: Sequence[KnowledgeBase] = (
                (await self.db.execute(select(KnowledgeBase))).scalars().all()
            )
        else:
            knowledge_bases: Sequence[KnowledgeBase] = (
                (
                    await self.db.execute(
                        select(KnowledgeBase)
                        .join(
                            knowledge_base_users,
                            KnowledgeBase.id
                            == knowledge_base_users.c.knowledge_base_id,
                        )
                        .filter(
                            and_(
                                knowledge_base_users.c.user_id == user_id,
                                KnowledgeBase.is_deleted == False,
                            )
                        )
                    )
                )
                .scalars()
                .all()
            )

        # 为每个知识库获取成员信息
        result = []
        for kb in knowledge_bases:
            # 获取知识库成员
            members = await self.db.execute(
                select(User, knowledge_base_users.c.permission).join(
                    knowledge_base_users,
                    and_(
                        User.id == knowledge_base_users.c.user_id,
                        knowledge_base_users.c.knowledge_base_id == kb.id,
                    ),
                )
            )

            # 构建成员列表
            member_list = []
            for member, permission in members:
                member_list.append(
                    {
                        "id": member.id,
                        "email": member.email,
                        "permission": (
                            permission.value if permission else None
                        ),  # 转换枚举为字符串
                        "is_owner": member.id == kb.owner_id,
                        "is_admin": member.is_admin,
                    }
                )

            # 构建知识库信息
            kb_dict = kb.to_dict()
            kb_dict["members"] = member_list
            result.append(kb_dict)

        return result

    async def get_knowledge_base_users(
        self, kb_id: int, current_user_id: int
    ) -> List[Dict[str, Any]]:
        """获取知识库的所有成员

        Args:
            kb_id (int): 知识库ID
            current_user_id (int): 当前用户ID

        Returns:
            List[Dict[str, Any]]: 成员列表，包含用户信息和权限信息

        Raises:
            HTTPException: 当用户没有权限时抛出
        """
        if not await self.check_permission(
            kb_id, current_user_id, PermissionType.VIEWER
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="没有足够的权限执行此操作"
            )

        # 获取知识库所有成员
        result = await self.db.execute(
            select(User, knowledge_base_users.c.permission)
            .join(knowledge_base_users, User.id == knowledge_base_users.c.user_id)
            .filter(knowledge_base_users.c.knowledge_base_id == kb_id)
        )

        users = []
        for user, permission in result:
            users.append(
                {
                    "id": user.id,
                    "email": user.email,
                    "permission": permission,
                    "is_owner": user.id
                    == (await self.get(kb_id, current_user_id)).owner_id,
                }
            )

        return users

    async def get_knowledge_base_members(
        self, kb_id: int, current_user_id: int
    ) -> KnowledgeBaseMemberList:
        """获取知识库成员列表"""
        kb = (
            await self.db.execute(
                select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
            )
        ).scalar_one_or_none()

        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在"
            )

        if not await kb.check_permission(
            self.db, current_user_id, PermissionType.VIEWER
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="没有足够的权限执行此操作"
            )

        members = await kb.get_all_members(self.db)
        return KnowledgeBaseMemberList(
            members=[KnowledgeBaseMemberInfo(**m) for m in members], total=len(members)
        )

    async def add_knowledge_base_member(
        self, kb_id: int, member_data: KnowledgeBaseMemberCreate, current_user_id: int
    ) -> None:
        """添加知识库成员"""
        kb = (
            await self.db.execute(
                select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
            )
        ).scalar_one_or_none()

        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在"
            )

        try:
            await kb.add_member(
                self.db, member_data.user_id, member_data.permission, current_user_id
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def update_knowledge_base_member(
        self,
        kb_id: int,
        user_id: int,
        member_data: KnowledgeBaseMemberUpdate,
        current_user_id: int,
    ) -> None:
        """更新知识库成员权限"""
        kb = (
            await self.db.execute(
                select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
            )
        ).scalar_one_or_none()

        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在"
            )

        try:
            await kb.update_member_permission(
                self.db, user_id, member_data.permission, current_user_id
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def remove_knowledge_base_member(
        self, kb_id: int, user_id: int, current_user_id: int
    ) -> None:
        """移除知识库成员"""
        kb = (
            await self.db.execute(
                select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
            )
        ).scalar_one_or_none()

        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在"
            )

        try:
            await kb.remove_member(self.db, user_id, current_user_id)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def check_training_queue(self) -> Optional[int]:
        """检查训练队列，获取下一个要训练的知识库ID

        Returns:
            Optional[int]: 下一个要训练的知识库ID，如果没有则返回None
        """
        try:
            # 创建训练管理器
            training_manager = RAGTrainingManager(self.db)

            # 检查队列
            next_kb_id = await training_manager.check_queue()

            if next_kb_id:
                Logger.info(f"找到下一个要训练的知识库: {next_kb_id}")

                # 更新状态为训练中
                await training_manager.update_training_status(
                    next_kb_id, TrainingStatus.TRAINING
                )

                # 启动训练任务
                train_knowledge_base(next_kb_id)

            return next_kb_id

        except Exception as e:
            Logger.error(f"检查训练队列失败: {str(e)}")
            return None

    async def get_training_queue_status(self, user_id: int) -> Dict[str, Any]:
        """获取训练队列状态

        Args:
            user_id: 用户ID

        Returns:
            Dict[str, Any]: 队列状态信息
        """
        try:
            # 检查用户是否为管理员
            user = (
                await self.db.execute(select(User).filter(User.id == user_id))
            ).scalar_one_or_none()

            if not user or not user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="只有管理员可以查看训练队列状态",
                )

            # 创建训练管理器
            training_manager = RAGTrainingManager(self.db)

            # 获取队列状态
            queue_status = await training_manager.get_queue_status()

            return queue_status

        except HTTPException:
            raise
        except Exception as e:
            Logger.error(f"获取训练队列状态失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取训练队列状态失败: {str(e)}",
            )

    async def check_kb_permission(
        self,
        kb_id: int,
        identity_id: Optional[int],
        required_permission: PermissionType,
    ) -> bool:
        """检查用户对知识库的权限"""
        if not identity_id:
            Logger.warning(
                f"Permission check failed: No identity provided for knowledge base {kb_id}"
            )
            return False

        # 获取用户身份信息
        identity = (
            await self.db.execute(
                select(UserIdentity).filter(UserIdentity.id == identity_id)
            )
        ).scalar_one_or_none()

        if not identity:
            Logger.warning(f"Permission check failed: Identity {identity_id} not found")
            return False

        kb = (
            await self.db.execute(
                select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
            )
        ).scalar_one_or_none()

        if not kb:
            Logger.warning(f"Permission check failed: Knowledge base {kb_id} not found")
            return False

        # 检查官方用户权限
        if identity.official_user_id:
            return await kb.check_permission(
                self.db, identity.official_user_id, required_permission
            )

        # 检查第三方用户权限
        if identity.third_party_user_id:
            # 第三方用户对自己的知识库有查看权限
            return True

        Logger.warning(
            f"Permission check failed: Identity {identity_id} "
            f"has no permission for knowledge base {kb_id}"
        )
        return False
    async def query_with_prompt_template(
        self,
        kb_id: int,
        user_context: UserContext,
        query: str,
        prompt_template_id: Optional[int] = None,
        method: str = RetrievalMethod.HYBRID_SEARCH,
        top_k: int = 5,
        use_rerank: bool = True,
        rerank_mode: str = RerankMode.WEIGHTED_SCORE,
        skip_permission_check: bool = False,
        template_variables: Optional[Dict[str, Any]] = None
    ) -> dict:
        """使用指定提示词模板进行RAG查询
        
        Args:
            kb_id: 知识库ID
            user_context: 用户上下文信息
            query: 用户查询内容
            prompt_template_id: 提示词模板ID，如果为None则使用知识库默认模板
            method: 检索方法
            top_k: 返回结果数量
            use_rerank: 是否使用重排序
            rerank_mode: 重排序模式
            skip_permission_check: 是否跳过权限检查
            template_variables: 模板变量值
            
        Returns:
            dict: 查询结果，包含渲染后的提示词和RAG响应
            
        Raises:
            HTTPException: 当权限不足、知识库不存在或模板不存在时
        """
        import time
        
        start_time = time.time()
        
        # 记录服务调用开始
        Logger.rag_service_start(
            service="KnowledgeBaseService",
            method="query_with_prompt_template",
            kb_id=kb_id,
            user_id=user_context.user_id,
        )
        
        Logger.info(
            f"使用提示词模板进行RAG查询: kb_id={kb_id}, "
            f"template_id={prompt_template_id}, user_id={user_context.user_id}"
        )
        
        try:
            # 检查知识库权限
            if not skip_permission_check:
                has_permission = await self.check_kb_permission(
                    kb_id=kb_id,
                    identity_id=user_context.identity_id,
                    required_permission=PermissionType.VIEWER,
                )
                
                if not has_permission:
                    Logger.warning(
                        f"查询被拒绝: 用户 {user_context.user_id} "
                        f"没有权限查询知识库 {kb_id}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="没有足够的权限执行此操作"
                    )
            
            # 获取知识库信息
            kb = (
                await self.db.execute(
                    select(KnowledgeBase).filter(
                        and_(KnowledgeBase.id == kb_id, KnowledgeBase.is_deleted == False)
                    )
                )
            ).scalar_one_or_none()
            
            if not kb:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="知识库不存在"
                )
            
            # 确定使用的提示词模板ID
            template_id_to_use = prompt_template_id
            if not template_id_to_use:
                # 使用知识库默认模板（如果有配置）
                template_id_to_use = getattr(kb, 'default_prompt_template_id', None)
            
            # 执行RAG检索获取上下文
            rag_result = await self.query_rag(
                kb_id=kb_id,
                user_context=user_context,
                query=query,
                method=method,
                top_k=top_k,
                use_rerank=use_rerank,
                rerank_mode=rerank_mode,
                skip_permission_check=True  # 已经检查过权限
            )
            
            # 提取检索到的上下文
            context_text = ""
            if "results" in rag_result and rag_result["results"]:
                context_chunks = []
                for result in rag_result["results"]:
                    if "content" in result:
                        context_chunks.append(result["content"])
                context_text = "\n\n".join(context_chunks)
            
            # 如果指定了提示词模板，进行模板渲染
            rendered_prompt = None
            template_info = None
            
            if template_id_to_use:
                try:
                    prompt_service = PromptService(self.db)
                    
                    # 准备模板变量
                    template_vars = {
                        "query": query,
                        "context": context_text,
                        "kb_name": kb.name,
                        "kb_description": kb.description or "",
                    }
                    
                    # 合并用户提供的变量
                    if template_variables:
                        template_vars.update(template_variables)
                    
                    # 渲染模板
                    render_result = await prompt_service.render_template(
                        template_id_to_use,
                        template_vars,
                        user_context.user_id
                    )
                    
                    rendered_prompt = render_result.rendered_content
                    
                    # 获取模板信息
                    template = await prompt_service.get_template(
                        template_id_to_use, 
                        user_context.user_id
                    )
                    
                    template_info = {
                        "id": template.id,
                        "name": template.name,
                        "version": "current",  # 可以扩展为具体版本
                        "variables_used": render_result.variables_used
                    }
                    
                    # 记录提示词使用统计
                    analytics_service = PromptAnalyticsService(self.db)
                    await analytics_service.log_usage(
                        template_id=template_id_to_use,
                        user_id=user_context.user_id,
                        kb_id=kb_id,
                        query=query,
                        variables_used=template_vars,
                        rendered_content=rendered_prompt,
                        execution_time=time.time() - start_time,
                        success=True
                    )
                    
                    Logger.info(f"提示词模板渲染成功: template_id={template_id_to_use}")
                    
                except Exception as e:
                    Logger.error(f"提示词模板处理失败: {str(e)}")
                    
                    # 记录失败统计
                    if template_id_to_use:
                        try:
                            analytics_service = PromptAnalyticsService(self.db)
                            await analytics_service.log_usage(
                                template_id=template_id_to_use,
                                user_id=user_context.user_id,
                                kb_id=kb_id,
                                query=query,
                                variables_used=template_variables or {},
                                execution_time=time.time() - start_time,
                                success=False,
                                error_message=str(e)
                            )
                        except:
                            pass  # 避免统计记录失败影响主流程
                    
                    # 如果模板处理失败，使用默认提示词
                    rendered_prompt = self._get_default_prompt(query, context_text)
                    template_info = {
                        "id": None,
                        "name": "默认模板",
                        "version": "default",
                        "error": str(e)
                    }
            else:
                # 没有指定模板，使用默认提示词
                rendered_prompt = self._get_default_prompt(query, context_text)
                template_info = {
                    "id": None,
                    "name": "默认模板",
                    "version": "default"
                }
            
            # 构建最终响应
            response = {
                "query": query,
                "kb_id": kb_id,
                "kb_name": kb.name,
                "template_info": template_info,
                "rendered_prompt": rendered_prompt,
                "context": context_text,
                "rag_results": rag_result.get("results", []),
                "retrieval_info": {
                    "method": method,
                    "top_k": top_k,
                    "use_rerank": use_rerank,
                    "total_results": len(rag_result.get("results", []))
                },
                "execution_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            }
            
            Logger.info(
                f"提示词模板查询完成: kb_id={kb_id}, "
                f"template_id={template_id_to_use}, "
                f"execution_time={response['execution_time']:.3f}s"
            )
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            Logger.error(f"提示词模板查询失败: {str(e)}")
            
            # 记录失败统计
            if prompt_template_id:
                try:
                    analytics_service = PromptAnalyticsService(self.db)
                    await analytics_service.log_usage(
                        template_id=prompt_template_id,
                        user_id=user_context.user_id,
                        kb_id=kb_id,
                        query=query,
                        variables_used=template_variables or {},
                        execution_time=time.time() - start_time,
                        success=False,
                        error_message=str(e)
                    )
                except:
                    pass  # 避免统计记录失败影响主流程
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"查询失败: {str(e)}"
            )
    
    def _get_default_prompt(self, query: str, context: str) -> str:
        """获取默认提示词
        
        Args:
            query: 用户查询
            context: 检索到的上下文
            
        Returns:
            str: 默认提示词内容
        """
        return f"""你是一个专业的AI助手，基于以下上下文信息回答用户问题。

上下文信息：
{context}

用户问题：
{query}

请基于上下文信息给出准确、有用的回答。如果上下文信息不足以回答问题，请明确说明。"""

    async def get_prompt_template_suggestions(
        self,
        kb_id: int,
        user_id: int,
        query_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取适合当前知识库的提示词模板建议
        
        Args:
            kb_id: 知识库ID
            user_id: 用户ID
            query_type: 查询类型（可选）
            
        Returns:
            List[Dict[str, Any]]: 推荐的模板列表
        """
        try:
            Logger.info(f"获取知识库 {kb_id} 的提示词模板建议")
            
            # 检查权限
            if not await self.check_permission(kb_id, user_id, PermissionType.VIEWER):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="没有足够的权限执行此操作"
                )
            
            prompt_service = PromptService(self.db)
            analytics_service = PromptAnalyticsService(self.db)
            
            # 获取用户可访问的模板
            templates, _ = await prompt_service.list_templates(
                user_id=user_id,
                page=1,
                page_size=50
            )
            
            # 获取在此知识库中使用最多的模板
            usage_stats = await analytics_service.get_usage_stats(
                kb_id=kb_id,
                include_trend=False
            )
            
            # 构建推荐列表
            suggestions = []
            
            # 添加使用统计信息
            usage_map = {stat.template_id: stat for stat in usage_stats}
            
            for template in templates:
                suggestion = {
                    "id": template.id,
                    "name": template.name,
                    "description": template.description,
                    "tags": template.tags or [],
                    "is_system": template.is_system,
                    "usage_in_kb": 0,
                    "success_rate": 0.0,
                    "avg_response_quality": None,
                    "recommendation_score": 0.0
                }
                
                # 添加使用统计
                if template.id in usage_map:
                    stat = usage_map[template.id]
                    suggestion.update({
                        "usage_in_kb": stat.total_usage,
                        "success_rate": stat.success_rate,
                        "avg_response_quality": stat.avg_response_quality
                    })
                
                # 计算推荐分数（基于使用量、成功率、质量等）
                score = 0.0
                if suggestion["usage_in_kb"] > 0:
                    score += min(suggestion["usage_in_kb"] * 0.1, 5.0)  # 使用量权重
                    score += suggestion["success_rate"] * 3.0  # 成功率权重
                    if suggestion["avg_response_quality"]:
                        score += suggestion["avg_response_quality"] * 2.0  # 质量权重
                
                # 系统模板额外加分
                if suggestion["is_system"]:
                    score += 1.0
                
                suggestion["recommendation_score"] = score
                suggestions.append(suggestion)
            
            # 按推荐分数排序
            suggestions.sort(key=lambda x: x["recommendation_score"], reverse=True)
            
            # 返回前10个推荐
            return suggestions[:10]
            
        except HTTPException:
            raise
        except Exception as e:
            Logger.error(f"获取提示词模板建议失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取模板建议失败: {str(e)}"
            )    asy
nc def set_default_prompt_template(
        self,
        kb_id: int,
        user_id: int,
        template_id: Optional[int],
        config: Optional[Dict[str, Any]] = None
    ) -> KnowledgeBase:
        """设置知识库的默认提示词模板
        
        Args:
            kb_id: 知识库ID
            user_id: 用户ID
            template_id: 提示词模板ID，None表示清除默认模板
            config: 提示词模板配置
            
        Returns:
            KnowledgeBase: 更新后的知识库对象
        """
        try:
            Logger.info(f"用户 {user_id} 为知识库 {kb_id} 设置默认提示词模板: {template_id}")
            
            # 检查权限（需要编辑权限）
            if not await self.check_permission(kb_id, user_id, PermissionType.EDITOR):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="没有足够的权限执行此操作"
                )
            
            # 获取知识库
            kb = (
                await self.db.execute(
                    select(KnowledgeBase).filter(
                        and_(KnowledgeBase.id == kb_id, KnowledgeBase.is_deleted == False)
                    )
                )
            ).scalar_one_or_none()
            
            if not kb:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="知识库不存在"
                )
            
            # 如果指定了模板ID，验证模板是否存在且用户有权限访问
            if template_id:
                prompt_service = PromptService(self.db)
                try:
                    await prompt_service.get_template(template_id, user_id)
                except HTTPException as e:
                    if e.status_code == 404:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="指定的提示词模板不存在"
                        )
                    elif e.status_code == 403:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="没有权限访问指定的提示词模板"
                        )
                    else:
                        raise
            
            # 设置默认模板
            await kb.set_default_prompt_template(self.db, template_id, config)
            
            # 记录审计日志
            await self.audit_manager.log_action(
                user_id=user_id,
                action="set_default_prompt_template",
                resource_type="knowledge_base",
                resource_id=kb_id,
                details={
                    "template_id": template_id,
                    "config": config
                }
            )
            
            Logger.info(f"知识库 {kb_id} 默认提示词模板设置成功")
            return kb
            
        except HTTPException:
            raise
        except Exception as e:
            Logger.error(f"设置默认提示词模板失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"设置默认模板失败: {str(e)}"
            )
    
    async def get_prompt_template_config(
        self,
        kb_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """获取知识库的提示词模板配置
        
        Args:
            kb_id: 知识库ID
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 提示词模板配置信息
        """
        try:
            Logger.info(f"用户 {user_id} 获取知识库 {kb_id} 的提示词模板配置")
            
            # 检查权限
            if not await self.check_permission(kb_id, user_id, PermissionType.VIEWER):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="没有足够的权限执行此操作"
                )
            
            # 获取知识库
            kb = (
                await self.db.execute(
                    select(KnowledgeBase).filter(
                        and_(KnowledgeBase.id == kb_id, KnowledgeBase.is_deleted == False)
                    )
                )
            ).scalar_one_or_none()
            
            if not kb:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="知识库不存在"
                )
            
            # 构建配置信息
            config = {
                "kb_id": kb_id,
                "kb_name": kb.name,
                "default_template_id": kb.default_prompt_template_id,
                "template_config": kb.get_prompt_template_config(),
                "selection_strategy": kb.get_template_selection_strategy(),
                "variable_mapping": kb.get_template_variable_mapping(),
                "supports_dynamic_selection": kb.supports_dynamic_template_selection()
            }
            
            # 如果有默认模板，获取模板信息
            if kb.default_prompt_template_id:
                try:
                    prompt_service = PromptService(self.db)
                    template = await prompt_service.get_template(
                        kb.default_prompt_template_id, 
                        user_id
                    )
                    config["default_template_info"] = {
                        "id": template.id,
                        "name": template.name,
                        "description": template.description,
                        "variables": template.variables or []
                    }
                except:
                    # 如果获取模板信息失败，不影响主流程
                    config["default_template_info"] = None
            
            # 获取推荐模板
            recommendations = await self.get_prompt_template_suggestions(kb_id, user_id)
            config["recommended_templates"] = recommendations
            
            return config
            
        except HTTPException:
            raise
        except Exception as e:
            Logger.error(f"获取提示词模板配置失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取模板配置失败: {str(e)}"
            )
    
    async def update_prompt_template_config(
        self,
        kb_id: int,
        user_id: int,
        config_update: Dict[str, Any]
    ) -> KnowledgeBase:
        """更新知识库的提示词模板配置
        
        Args:
            kb_id: 知识库ID
            user_id: 用户ID
            config_update: 配置更新数据
            
        Returns:
            KnowledgeBase: 更新后的知识库对象
        """
        try:
            Logger.info(f"用户 {user_id} 更新知识库 {kb_id} 的提示词模板配置")
            
            # 检查权限
            if not await self.check_permission(kb_id, user_id, PermissionType.EDITOR):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="没有足够的权限执行此操作"
                )
            
            # 获取知识库
            kb = (
                await self.db.execute(
                    select(KnowledgeBase).filter(
                        and_(KnowledgeBase.id == kb_id, KnowledgeBase.is_deleted == False)
                    )
                )
            ).scalar_one_or_none()
            
            if not kb:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="知识库不存在"
                )
            
            # 获取当前配置
            current_config = kb.get_prompt_template_config()
            
            # 合并配置更新
            updated_config = {**current_config, **config_update}
            
            # 验证配置
            self._validate_prompt_template_config(updated_config)
            
            # 更新配置
            kb.prompt_template_config = updated_config
            kb.updated_at = datetime.now()
            
            self.db.add(kb)
            await self.db.commit()
            
            # 记录审计日志
            await self.audit_manager.log_action(
                user_id=user_id,
                action="update_prompt_template_config",
                resource_type="knowledge_base",
                resource_id=kb_id,
                details={
                    "config_update": config_update,
                    "updated_config": updated_config
                }
            )
            
            Logger.info(f"知识库 {kb_id} 提示词模板配置更新成功")
            return kb
            
        except HTTPException:
            raise
        except Exception as e:
            Logger.error(f"更新提示词模板配置失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新模板配置失败: {str(e)}"
            )
    
    def _validate_prompt_template_config(self, config: Dict[str, Any]) -> None:
        """验证提示词模板配置
        
        Args:
            config: 配置数据
            
        Raises:
            HTTPException: 当配置无效时
        """
        # 验证选择策略
        valid_strategies = ["default", "dynamic", "user_choice"]
        strategy = config.get("selection_strategy", "default")
        if strategy not in valid_strategies:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的模板选择策略: {strategy}，支持的策略: {valid_strategies}"
            )
        
        # 验证变量映射
        variable_mapping = config.get("variable_mapping", {})
        if not isinstance(variable_mapping, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="变量映射必须是字典格式"
            )
        
        # 验证推荐配置
        recommendations = config.get("recommendations", {})
        if not isinstance(recommendations, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="推荐配置必须是字典格式"
            )
        
        # 验证推荐模板ID列表
        for query_type, template_ids in recommendations.items():
            if not isinstance(template_ids, list):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"推荐模板ID列表必须是数组格式: {query_type}"
                )
            
            for template_id in template_ids:
                if not isinstance(template_id, int) or template_id <= 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"无效的模板ID: {template_id}"
                    )