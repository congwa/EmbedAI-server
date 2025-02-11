from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.knowledge_base import KnowledgeBase, TrainingStatus
from app.models.document import Document
from app.models.user import User
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    QueryRequest,
    QueryResponse
)
from app.utils.session import SessionManager
from app.utils.rate_limit import rate_limit
from app.core.config import settings

class KnowledgeBaseService:
    def __init__(self, db: Session):
        self.db = db
        self.session_manager = SessionManager()

    async def create(self, kb_in: KnowledgeBaseCreate, user_id: int) -> KnowledgeBase:
        """创建新知识库

        Args:
            kb_in (KnowledgeBaseCreate): 知识库创建模型
            user_id (int): 要绑定的普通用户ID

        Returns:
            KnowledgeBase: 创建成功的知识库对象

        Raises:
            ValueError: 当用户不存在、已绑定知识库或无权限时抛出
        """
        # 检查用户是否存在且未绑定知识库
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        if user.is_admin:
            raise ValueError("Cannot bind knowledge base to admin user")

        # 检查用户是否已经绑定了知识库
        if self.db.query(KnowledgeBase).filter(KnowledgeBase.owner_id == user_id).first():
            raise ValueError("User already has a knowledge base")

        # 验证管理员权限
        admin_user = self.db.query(User).filter(User.id == user.created_by_id).first()
        if not admin_user or not admin_user.is_admin:
            raise ValueError("User was not created by an admin user")

        # 创建工作目录
        working_dir = f"kb_{user_id}"

        # 创建知识库
        kb = KnowledgeBase(
            name=kb_in.name,
            domain=kb_in.domain,
            example_queries=kb_in.example_queries,
            entity_types=kb_in.entity_types,
            llm_config=kb_in.llm_config.model_dump(),
            working_dir=working_dir,
            owner_id=user_id
        )

        self.db.add(kb)
        self.db.commit()
        self.db.refresh(kb)

        return kb

    async def train(self, kb_id: int) -> KnowledgeBase:
        """训练知识库

        Args:
            kb_id (int): 知识库ID

        Returns:
            KnowledgeBase: 更新后的知识库对象

        Raises:
            ValueError: 当知识库不存在或不能训练时抛出
        """
        kb = self.db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            raise ValueError("Knowledge base not found")

        if not kb.can_train:
            raise ValueError("Knowledge base cannot be trained in current status")

        # 获取知识库的所有未删除文档
        documents = self.db.query(Document).filter(
            Document.knowledge_base_id == kb_id,
            Document.is_deleted == False
        ).all()

        if not documents:
            raise ValueError("No documents available for training")

        # 检查是否启用训练队列
        if settings.ENABLE_TRAINING_QUEUE:
            # 检查是否有其他知识库正在训练
            training_kb = self.db.query(KnowledgeBase).filter(
                KnowledgeBase.training_status == TrainingStatus.TRAINING
            ).first()

            if training_kb:
                # 如果有其他知识库在训练，将当前知识库设置为排队状态
                kb.training_status = TrainingStatus.QUEUED
                kb.queued_at = datetime.now()
                kb.training_error = None  # 清除之前的错误信息
                self.db.commit()
                self.db.refresh(kb)
                return kb

        # 更新训练状态为排队中
        kb.training_status = TrainingStatus.QUEUED
        kb.queued_at = datetime.now()
        kb.training_error = None
        kb.training_started_at = None  # 重置开始时间
        kb.training_finished_at = None  # 重置结束时间
        self.db.commit()
        self.db.refresh(kb)

        # 启动异步训练任务
        from app.utils.tasks import train_knowledge_base
        train_knowledge_base(kb_id)

        return kb

    async def query(self, kb_id: int, request: QueryRequest) -> QueryResponse:
        kb = self.db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            raise ValueError("Knowledge base not found")

        if not kb.can_query:
            raise ValueError("Knowledge base is not ready for querying")

        # 获取会话
        session = await self.session_manager.get_session(
            str(kb_id),
            kb.llm_config
        )

        # 执行查询
        result = session.grag.query(
            request.query,
            params=request.model_dump(exclude={"query"})
        )

        return QueryResponse(
            response=result.response,
            context={
                "entities": [str(e) for e in result.context.entities],
                "relationships": [str(r) for r in result.context.relationships],
                "chunks": [str(c) for c in result.context.chunks]
            } if result.context else None
        )

    async def get_by_id(self, kb_id: int) -> Optional[KnowledgeBase]:
        return self.db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()

    async def update(self, kb_id: int, kb_update: KnowledgeBaseUpdate, admin_id: int) -> KnowledgeBase:
        """更新知识库信息

        Args:
            kb_id (int): 知识库ID
            kb_update (KnowledgeBaseUpdate): 知识库更新模型
            admin_id (int): 管理员用户ID

        Returns:
            KnowledgeBase: 更新后的知识库对象

        Raises:
            ValueError: 当知识库不存在或管理员无权限时抛出
        """
        # 获取知识库
        kb = self.db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            raise ValueError("Knowledge base not found")

        # 验证管理员权限
        if kb.owner.created_by_id != admin_id:
            raise ValueError("Admin user does not have permission to update this knowledge base")

        # 更新数据
        update_data = kb_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(kb, field, value)

        self.db.commit()
        self.db.refresh(kb)
        return kb