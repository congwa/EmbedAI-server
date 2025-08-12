"""
知识库训练服务
负责知识库的训练、训练队列管理和训练状态管理
"""
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.knowledge_base import KnowledgeBase, TrainingStatus, PermissionType
from app.models.document import Document
from app.models.user import User
from app.schemas.identity import UserContext, UserType
from app.rag.training.training_manager import RAGTrainingManager
from app.services.audit import AuditManager
from app.utils.tasks import train_knowledge_base
from app.core.logger import Logger


class KnowledgeBaseTrainingService:
    """知识库训练服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.audit_manager = AuditManager(db)

    async def train(self, kb_id: int, user_id: int) -> KnowledgeBase:
        """训练知识库"""
        import time

        start_time = time.time()

        # 记录服务调用开始
        Logger.rag_service_start(
            service="KnowledgeBaseTrainingService", method="train", kb_id=kb_id, user_id=user_id
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
            from app.services.knowledge.knowledge_base_core import KnowledgeBaseCoreService
            core_service = KnowledgeBaseCoreService(self.db)
            permission_granted = await core_service.check_permission(
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
            from app.core.config import settings
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
                service="KnowledgeBaseTrainingService",
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
                service="KnowledgeBaseTrainingService",
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
                service="KnowledgeBaseTrainingService",
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