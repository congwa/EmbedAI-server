"""
知识库成员管理服务
负责知识库成员的添加、删除、权限管理和用户权限检查
"""
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, select
from fastapi import HTTPException, status

from app.models.knowledge_base import (
    KnowledgeBase,
    knowledge_base_users,
    PermissionType,
)
from app.models.user import User
from app.schemas.knowledge_base import (
    KnowledgeBasePermissionCreate,
    KnowledgeBasePermissionUpdate,
    KnowledgeBaseMemberList,
    KnowledgeBaseMemberInfo,
    KnowledgeBaseMemberCreate,
    KnowledgeBaseMemberUpdate,
)
from app.core.logger import Logger


class KnowledgeBaseMembersService:
    """知识库成员管理服务"""
    
    def __init__(self, db: Session):
        self.db = db

    async def add_user(
        self,
        kb_id: int,
        permission_data: KnowledgeBasePermissionCreate,
        current_user_id: int,
    ) -> None:
        """添加用户到知识库"""
        from app.services.knowledge.knowledge_base_core import KnowledgeBaseCoreService
        core_service = KnowledgeBaseCoreService(self.db)
        
        if not await core_service.check_permission(
            kb_id, current_user_id, PermissionType.ADMIN
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="没有足够的权限执行此操作"
            )

        # 检查用户是否已有权限
        existing_permission = await core_service.get_user_permission(
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
        from app.services.knowledge.knowledge_base_core import KnowledgeBaseCoreService
        core_service = KnowledgeBaseCoreService(self.db)
        
        if not await core_service.check_permission(
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
        from app.services.knowledge.knowledge_base_core import KnowledgeBaseCoreService
        core_service = KnowledgeBaseCoreService(self.db)
        
        if not await core_service.check_permission(
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
        from app.services.knowledge.knowledge_base_core import KnowledgeBaseCoreService
        core_service = KnowledgeBaseCoreService(self.db)
        
        if not await core_service.check_permission(
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
                    == (await core_service.get(kb_id, current_user_id)).owner_id,
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