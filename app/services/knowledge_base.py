from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
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
    KnowledgeBasePermissionUpdate,
    KnowledgeBaseMemberList,
    KnowledgeBaseMemberInfo,
    KnowledgeBaseMemberCreate,
    KnowledgeBaseMemberUpdate
)
from app.utils.session import SessionManager
from app.utils.rate_limit import rate_limit
from app.core.config import settings
from sqlalchemy.sql import select

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
        user = (await self.db.execute(
            select(User).filter(User.id == user_id)
        )).scalar_one_or_none()
        
        if user and user.is_admin:
            return True
            
        # 查询用户权限
        permission = (await self.db.execute(
            select(knowledge_base_users).filter(
                and_(
                    knowledge_base_users.c.knowledge_base_id == kb_id,
                    knowledge_base_users.c.user_id == user_id
                )
            )
        )).first()
        
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
        permission = (await self.db.execute(
            select(knowledge_base_users).filter(
                and_(
                    knowledge_base_users.c.knowledge_base_id == kb_id,
                    knowledge_base_users.c.user_id == user_id
                )
            )
        )).first()
        
        return permission.permission if permission else None

    async def create(
        self,
        kb: KnowledgeBaseCreate,
        owner_id: int
    ) -> KnowledgeBase:
        """创建新知识库"""
        # 使用默认配置
        llm_config = settings.DEFAULT_LLM_CONFIG
        if kb.llm_config:
            # 合并用户配置
            if "llm" in kb.llm_config.model_dump():
                llm_config.llm = kb.llm_config.llm
            if "embeddings" in kb.llm_config.model_dump():
                llm_config.embeddings = kb.llm_config.embeddings
            
        db_kb = KnowledgeBase(
            name=kb.name,
            owner_id=owner_id,
            domain=kb.domain,
            example_queries=kb.example_queries or [],
            entity_types=kb.entity_types or [],
            llm_config=llm_config.model_dump(),  # 转换为字典
            training_status=TrainingStatus.INIT
        )
        
        self.db.add(db_kb)
        await self.db.commit()
        await self.db.refresh(db_kb)
        
        # 添加所有者权限
        await self.db.execute(
            knowledge_base_users.insert().values(
                knowledge_base_id=db_kb.id,
                user_id=owner_id,
                permission=PermissionType.OWNER
            )
        )
        
        await self.db.commit()
        await self.db.refresh(db_kb)
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
            
        kb = (await self.db.execute(
            select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
        )).scalar_one_or_none()
        
        if not kb:
            raise ValueError("Knowledge base not found")

        # 获取知识库的所有未删除文档
        documents = (await self.db.execute(
            select(Document).filter(
                Document.knowledge_base_id == kb_id,
                Document.is_deleted == False
            )
        )).scalars().all()

        if not documents:
            raise ValueError("No documents available for training")

        # 检查是否启用训练队列
        if settings.ENABLE_TRAINING_QUEUE:
            # 检查是否有其他知识库正在训练
            training_kb = (await self.db.execute(
                select(KnowledgeBase).filter(
                    KnowledgeBase.training_status == TrainingStatus.TRAINING
                )
            )).scalar_one_or_none()

            if training_kb:
                # 如果有其他知识库在训练，将当前知识库设置为排队状态
                kb.training_status = TrainingStatus.QUEUED
                kb.queued_at = datetime.now()
                kb.training_error = None  # 清除之前的错误信息
                await self.db.commit()
                await self.db.refresh(kb)
                return kb

        # 如果没有其他知识库在训练，直接开始训练
        kb.training_status = TrainingStatus.TRAINING
        kb.training_started_at = datetime.now()
        kb.training_error = None
        kb.queued_at = None
        await self.db.commit()
        await self.db.refresh(kb)

        # 启动异步训练任务
        from app.utils.tasks import train_knowledge_base
        train_knowledge_base(kb_id)

        return kb

    async def query(
        self,
        kb_id: int,
        user_id: int,
        query: str,
        top_k: int = 5
    ) -> dict:
        """查询知识库

        Args:
            kb_id (int): 知识库ID
            user_id (int): 用户ID
            query (str): 查询内容
            top_k (int, optional): 返回结果数量. Defaults to 5.

        Returns:
            dict: 查询结果
        """
        # 检查权限
        if not await self.check_permission(kb_id, user_id, PermissionType.VIEWER):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有足够的权限执行此操作"
            )
            
        kb = (await self.db.execute(
            select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
        )).scalar_one_or_none()
        
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="知识库不存在"
            )

        if kb.training_status != TrainingStatus.TRAINED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="知识库尚未训练完成"
            )

        # 获取会话
        session = self.session_manager.get_session_sync(
            str(kb_id),
            kb.llm_config
        )

        # 执行查询
        result = session.query(query, top_k=top_k)

        return {
            "query": query,
            "results": result,
            "metadata": {
                "kb_id": kb_id,
                "top_k": top_k
            }
        }

    async def get(self, kb_id: int, user_id: int) -> KnowledgeBase:
        """获取知识库详情

        Args:
            kb_id (int): 知识库ID
            user_id (int): 用户ID

        Returns:
            KnowledgeBase: 知识库对象，包含成员信息

        Raises:
            HTTPException: 当用户没有权限或知识库不存在时抛出
        """
        if not await self.check_permission(kb_id, user_id, PermissionType.VIEWER):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有足够的权限执行此操作"
            )
            
        kb = (await self.db.execute(
            select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
        )).scalar_one_or_none()
        
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="知识库不存在"
            )
            
        # 获取知识库成员
        members = await self.db.execute(
            select(User, knowledge_base_users.c.permission)
            .join(
                knowledge_base_users,
                User.id == knowledge_base_users.c.user_id
            )
            .filter(knowledge_base_users.c.knowledge_base_id == kb_id)
        )
        
        # 构建成员列表
        member_list = []
        for member, permission in members:
            member_list.append({
                "id": member.id,
                "email": member.email,
                "permission": permission,
                "is_owner": member.id == kb.owner_id,
                "is_admin": member.is_admin
            })
            
        # 将成员列表添加到知识库对象中
        kb.members = member_list
            
        return kb

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
            
        db_kb = (await self.db.execute(
            select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
        )).scalar_one_or_none()
        
        if not db_kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="知识库不存在"
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
        kb = (await self.db.execute(
            select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
        )).scalar_one_or_none()
        
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
        kb = (await self.db.execute(
            select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
        )).scalar_one_or_none()
        
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
    ) -> List[Dict[str, Any]]:
        """获取用户可访问的所有知识库，并包含成员信息

        Args:
            user_id (int): 用户ID

        Returns:
            List[Dict[str, Any]]: 知识库列表，每个知识库包含成员信息
        """
        user = (await self.db.execute(
            select(User).filter(User.id == user_id)
        )).scalar_one_or_none()
        
        # 获取知识库列表
        if user.is_admin:
            knowledge_bases = (await self.db.execute(select(KnowledgeBase))).scalars().all()
        else:
            knowledge_bases = (await self.db.execute(
                select(KnowledgeBase).join(
                    knowledge_base_users,
                    KnowledgeBase.id == knowledge_base_users.c.knowledge_base_id
                ).filter(
                    knowledge_base_users.c.user_id == user_id
                )
            )).scalars().all()
        
        # 为每个知识库获取成员信息
        result = []
        for kb in knowledge_bases:
            # 获取知识库成员
            members = await self.db.execute(
                select(User, knowledge_base_users.c.permission)
                .join(
                    knowledge_base_users,
                    and_(
                        User.id == knowledge_base_users.c.user_id,
                        knowledge_base_users.c.knowledge_base_id == kb.id
                    )
                )
            )
            
            # 构建成员列表
            member_list = []
            for member, permission in members:
                member_list.append({
                    "id": member.id,
                    "email": member.email,
                    "permission": permission.value if permission else None,  # 转换枚举为字符串
                    "is_owner": member.id == kb.owner_id,
                    "is_admin": member.is_admin
                })
            
            # 构建知识库信息
            kb_dict = kb.to_dict()
            kb_dict["members"] = member_list
            result.append(kb_dict)
        
        return result

    async def get_knowledge_base_users(
        self,
        kb_id: int,
        current_user_id: int
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
        if not await self.check_permission(kb_id, current_user_id, PermissionType.VIEWER):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有足够的权限执行此操作"
            )
        
        # 获取知识库所有成员
        result = await self.db.execute(
            select(User, knowledge_base_users.c.permission)
            .join(
                knowledge_base_users,
                User.id == knowledge_base_users.c.user_id
            )
            .filter(knowledge_base_users.c.knowledge_base_id == kb_id)
        )
        
        users = []
        for user, permission in result:
            users.append({
                "id": user.id,
                "email": user.email,
                "permission": permission,
                "is_owner": user.id == (await self.get(kb_id, current_user_id)).owner_id
            })
        
        return users

    async def get_knowledge_base_members(
        self,
        kb_id: int,
        current_user_id: int
    ) -> KnowledgeBaseMemberList:
        """获取知识库成员列表
        
        Args:
            kb_id: 知识库ID
            current_user_id: 当前用户ID
            
        Returns:
            KnowledgeBaseMemberList: 成员列表响应
            
        Raises:
            HTTPException: 当用户没有权限或知识库不存在时
        """
        if not await self.check_permission(kb_id, current_user_id, PermissionType.VIEWER):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有足够的权限执行此操作"
            )
            
        # 获取知识库所有成员
        members = await self.db.execute(
            select(User, knowledge_base_users.c.permission)
            .join(
                knowledge_base_users,
                User.id == knowledge_base_users.c.user_id
            )
            .filter(knowledge_base_users.c.knowledge_base_id == kb_id)
        )
        
        member_list = []
        for member, permission in members:
            member_list.append({
                "id": member.id,
                "email": member.email,
                "permission": permission.value if permission else None,
                "is_owner": member.id == (await self.get(kb_id, current_user_id)).owner_id,
                "is_admin": member.is_admin
            })
            
        return KnowledgeBaseMemberList(
            members=[KnowledgeBaseMemberInfo(**m) for m in member_list],
            total=len(member_list)
        )
        
    async def add_knowledge_base_member(
        self,
        kb_id: int,
        member_data: KnowledgeBaseMemberCreate,
        current_user_id: int
    ) -> None:
        """添加知识库成员
        
        Args:
            kb_id: 知识库ID
            member_data: 成员信息
            current_user_id: 当前用户ID
            
        Raises:
            HTTPException: 当用户没有权限、知识库不存在或操作失败时
        """
        kb = await self.get(kb_id)
        try:
            await kb.add_member(
                member_data.user_id,
                member_data.permission,
                current_user_id
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
            
    async def update_knowledge_base_member(
        self,
        kb_id: int,
        user_id: int,
        member_data: KnowledgeBaseMemberUpdate,
        current_user_id: int
    ) -> None:
        """更新知识库成员权限
        
        Args:
            kb_id: 知识库ID
            user_id: 目标用户ID
            member_data: 更新的权限信息
            current_user_id: 当前用户ID
            
        Raises:
            HTTPException: 当用户没有权限、知识库不存在或操作失败时
        """
        kb = await self.get(kb_id)
        try:
            await kb.update_member_permission(
                user_id,
                member_data.permission,
                current_user_id
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
            
    async def remove_knowledge_base_member(
        self,
        kb_id: int,
        user_id: int,
        current_user_id: int
    ) -> None:
        """移除知识库成员
        
        Args:
            kb_id: 知识库ID
            user_id: 要移除的用户ID
            current_user_id: 当前用户ID
            
        Raises:
            HTTPException: 当用户没有权限、知识库不存在或操作失败时
        """
        kb = await self.get(kb_id)
        try:
            await kb.remove_member(user_id, current_user_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )