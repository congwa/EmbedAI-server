"""
知识库核心服务
负责知识库的基础CRUD操作和权限检查
"""
from typing import Optional, List, Dict, Any
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
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
)
from app.core.config import settings
from app.core.logger import Logger
from app.services.audit import AuditManager


class KnowledgeBaseCoreService:
    """知识库核心服务"""
    
    def __init__(self, db: Session):
        self.db = db
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
            service="KnowledgeBaseCoreService", method="create", user_id=owner_id
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
            service="KnowledgeBaseCoreService",
            method="create",
            duration=process_time,
            result_summary={
                "kb_id": db_kb.id,
                "kb_name": db_kb.name,
                "owner_id": owner_id,
                "working_dir": working_dir,
            },
        )

        Logger.info(
            f"Knowledge base '{kb.name}' (ID: {db_kb.id}) created successfully with working directory: {working_dir}"
        )
        return db_kb

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
            knowledge_bases = (
                (await self.db.execute(select(KnowledgeBase))).scalars().all()
            )
        else:
            knowledge_bases = (
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
        from app.models.identity import UserIdentity
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