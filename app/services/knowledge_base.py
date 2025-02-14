from pathlib import Path
from typing import Optional, Tuple, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException, status
from app.models.knowledge_base import KnowledgeBase, TrainingStatus, knowledge_base_users, PermissionType
from app.models.document import Document
from app.models.user import User
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    QueryRequest,
    QueryResponse,
    KnowledgeBasePermissionCreate,
    KnowledgeBasePermissionUpdate
)
from app.utils.session import SessionManager
from app.utils.rate_limit import rate_limit
from app.core.config import settings

class KnowledgeBaseService:
    def __init__(self, db: Session):
        self.db = db
        self.session_manager = SessionManager()

    async def check_permission(
        self,
        kb_id: int,
        user_id: int,
        required_permission: PermissionType
    ) -> bool:
        """检查用户对知识库的权限"""
        # 管理员用户拥有所有权限
        user = await self.db.query(User).filter(User.id == user_id).first()
        if user and user.is_admin:
            return True
            
        # 查询用户权限
        permission = await self.db.query(knowledge_base_users).filter(
            and_(
                knowledge_base_users.c.knowledge_base_id == kb_id,
                knowledge_base_users.c.user_id == user_id
            )
        ).first()
        
        if not permission:
            return False
            
        # 权限等级检查
        permission_levels = {
            PermissionType.VIEWER: 0,
            PermissionType.EDITOR: 1,
            PermissionType.ADMIN: 2,
            PermissionType.OWNER: 3
        }
        
        return permission_levels[permission.permission] >= permission_levels[required_permission]

    async def get_user_permission(
        self,
        kb_id: int,
        user_id: int
    ) -> Optional[PermissionType]:
        """获取用户对知识库的权限级别"""
        permission = await self.db.query(knowledge_base_users).filter(
            and_(
                knowledge_base_users.c.knowledge_base_id == kb_id,
                knowledge_base_users.c.user_id == user_id
            )
        ).first()
        
        return permission.permission if permission else None

    async def create(
        self,
        kb: KnowledgeBaseCreate,
        owner_id: int
    ) -> KnowledgeBase:
        """创建知识库"""
        db_kb = KnowledgeBase(
            **kb.model_dump(),
            owner_id=owner_id
        )
        self.db.add(db_kb)
        await self.db.flush()
        
        # 为创建者添加所有者权限
        await self.db.execute(
            knowledge_base_users.insert().values(
                knowledge_base_id=db_kb.id,
                user_id=owner_id,
                permission=PermissionType.OWNER
            )
        )
        
        await self.db.commit()
        return db_kb

    async def train(
        self,
        kb_id: int,
        user_id: int
    ) -> KnowledgeBase:
        """训练知识库"""
        if not await self.check_permission(kb_id, user_id, PermissionType.EDITOR):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有足够的权限执行此操作"
            )
            
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

    async def update(
        self,
        kb_id: int,
        kb: KnowledgeBaseUpdate,
        user_id: int
    ) -> KnowledgeBase:
        """更新知识库"""
        if not await self.check_permission(kb_id, user_id, PermissionType.EDITOR):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有足够的权限执行此操作"
            )
            
        db_kb = await self.db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not db_kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="知识库不存在"
            )
            
        for field, value in kb.model_dump(exclude_unset=True).items():
            setattr(db_kb, field, value)
            
        await self.db.commit()
        return db_kb

    async def add_user(
        self,
        kb_id: int,
        permission_data: KnowledgeBasePermissionCreate,
        current_user_id: int
    ) -> None:
        """添加用户到知识库"""
        if not await self.check_permission(kb_id, current_user_id, PermissionType.ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有足够的权限执行此操作"
            )
            
        # 检查用户是否已有权限
        existing_permission = await self.get_user_permission(kb_id, permission_data.user_id)
        if existing_permission:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户已经拥有此知识库的权限"
            )
            
        await self.db.execute(
            knowledge_base_users.insert().values(
                knowledge_base_id=kb_id,
                user_id=permission_data.user_id,
                permission=permission_data.permission
            )
        )
        await self.db.commit()

    async def update_user_permission(
        self,
        kb_id: int,
        user_id: int,
        permission_data: KnowledgeBasePermissionUpdate,
        current_user_id: int
    ) -> None:
        """更新用户的知识库权限"""
        if not await self.check_permission(kb_id, current_user_id, PermissionType.ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有足够的权限执行此操作"
            )
            
        # 不能修改所有者的权限
        kb = await self.db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if kb.owner_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能修改知识库所有者的权限"
            )
            
        await self.db.execute(
            knowledge_base_users.update()
            .where(
                and_(
                    knowledge_base_users.c.knowledge_base_id == kb_id,
                    knowledge_base_users.c.user_id == user_id
                )
            )
            .values(permission=permission_data.permission)
        )
        await self.db.commit()

    async def remove_user(
        self,
        kb_id: int,
        user_id: int,
        current_user_id: int
    ) -> None:
        """从知识库中移除用户"""
        if not await self.check_permission(kb_id, current_user_id, PermissionType.ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有足够的权限执行此操作"
            )
            
        # 不能移除所有者
        kb = await self.db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if kb.owner_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能移除知识库所有者"
            )
            
        await self.db.execute(
            knowledge_base_users.delete().where(
                and_(
                    knowledge_base_users.c.knowledge_base_id == kb_id,
                    knowledge_base_users.c.user_id == user_id
                )
            )
        )
        await self.db.commit()

    async def get_user_knowledge_bases(
        self,
        user_id: int
    ) -> List[KnowledgeBase]:
        """获取用户可访问的所有知识库"""
        user = await self.db.query(User).filter(User.id == user_id).first()
        
        # 管理员可以看到所有知识库
        if user.is_admin:
            return await self.db.query(KnowledgeBase).all()
            
        # 普通用户只能看到自己有权限的知识库
        return await self.db.query(KnowledgeBase).join(
            knowledge_base_users,
            KnowledgeBase.id == knowledge_base_users.c.knowledge_base_id
        ).filter(
            knowledge_base_users.c.user_id == user_id
        ).all()