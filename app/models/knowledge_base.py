from sqlalchemy import Column, Integer, String, ForeignKey, JSON, ARRAY, DateTime, Enum
from sqlalchemy.orm import relationship

from .database import Base
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.schemas.base import CustomBaseModel
from sqlalchemy.sql import select, and_
from .associations import knowledge_base_users
from .enums import PermissionType, TrainingStatus
from app.models import User

class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    domain = Column(String, nullable=False)
    example_queries = Column(JSON, nullable=False)
    entity_types = Column(JSON, nullable=False)
    llm_config = Column(JSON, nullable=True)
    working_dir = Column(String, nullable=True)
    
    # 时间字段
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    # 训练相关字段
    training_status = Column(Enum(TrainingStatus), nullable=False, default=TrainingStatus.INIT)
    training_started_at = Column(DateTime, nullable=True)
    training_finished_at = Column(DateTime, nullable=True)
    training_error = Column(String, nullable=True)
    queued_at = Column(DateTime, nullable=True)
    
    # 关系定义
    owner = relationship("User", back_populates="owned_knowledge_bases", foreign_keys=[owner_id])
    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan")
    users = relationship(
        "User", 
        secondary=knowledge_base_users,
        back_populates="knowledge_bases",
        cascade="all, delete",
        passive_deletes=True
    )
    
    @property
    def can_train(self) -> bool:
        return self.training_status in [TrainingStatus.INIT, TrainingStatus.FAILED]
    
    @property
    def can_query(self) -> bool:
        return self.training_status == TrainingStatus.TRAINED

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，用于 JSON 序列化
        
        使用 Pydantic 的序列化方式处理时间字段，确保时间格式的一致性
        
        Returns:
            Dict[str, Any]: 包含所有字段的字典，时间字段会被格式化为 ISO 格式字符串
        """
        from app.schemas.knowledge_base import KnowledgeBase as KnowledgeBaseSchema
        from app.schemas.llm import LLMConfig
        
        # 如果 llm_config 是字典，转换为 LLMConfig 对象
        if isinstance(self.llm_config, dict):
            self.llm_config = LLMConfig.model_validate(self.llm_config)
            
        # 使用 Pydantic 模型进行序列化
        schema = KnowledgeBaseSchema.model_validate(self)
        result = schema.model_dump(mode='json')
        
        # 处理成员列表中的枚举值
        if result.get('members'):
            for member in result['members']:
                if 'permission' in member and isinstance(member['permission'], PermissionType):
                    member['permission'] = member['permission'].value
                    
        return result
        
    async def get_member_permission(self, user_id: int) -> Optional[PermissionType]:
        """获取用户在知识库中的权限
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[PermissionType]: 用户权限，如果不是成员则返回None
        """
        result = await self.db.execute(
            select(knowledge_base_users.c.permission)
            .where(
                and_(
                    knowledge_base_users.c.knowledge_base_id == self.id,
                    knowledge_base_users.c.user_id == user_id
                )
            )
        )
        row = result.first()
        return row.permission if row else None
        
    async def check_permission(
        self,
        user_id: int,
        required_permission: PermissionType
    ) -> bool:
        """检查用户对知识库的权限
        
        Args:
            user_id: 用户ID
            required_permission: 所需的权限级别
            
        Returns:
            bool: 是否有权限
        """
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
                    knowledge_base_users.c.knowledge_base_id == self.id,
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
        
    async def get_all_members(self) -> List[Dict[str, Any]]:
        """获取所有成员信息
        
        Returns:
            List[Dict[str, Any]]: 成员列表
        """
        result = await self.db.execute(
            select(User, knowledge_base_users.c.permission)
            .join(
                knowledge_base_users,
                and_(
                    User.id == knowledge_base_users.c.user_id,
                    knowledge_base_users.c.knowledge_base_id == self.id
                )
            )
        )
        
        members = []
        for user, permission in result:
            members.append({
                "id": user.id,
                "email": user.email,
                "permission": permission,
                "is_owner": user.id == self.owner_id,
                "is_admin": user.is_admin
            })
        return members
        
    async def add_member(
        self,
        user_id: int,
        permission: PermissionType,
        current_user_id: int
    ) -> None:
        """添加成员
        
        Args:
            user_id: 要添加的用户ID
            permission: 权限级别
            current_user_id: 当前操作用户ID
            
        Raises:
            ValueError: 当用户已是成员或没有足够权限时
        """
        # 检查是否已是成员
        if await self.get_member_permission(user_id):
            raise ValueError("用户已是知识库成员")
            
        # 检查操作权限
        if not await self.check_permission(current_user_id, PermissionType.ADMIN):
            raise ValueError("没有足够的权限执行此操作")
            
        # 获取当前用户有效权限
        current_permission = await self.get_effective_permission(current_user_id)
        if not current_permission:
            raise ValueError("没有足够的权限执行此操作")
            
        # 不能添加权限级别高于或等于自己的成员
        if PermissionType.get_permission_level(permission) >= PermissionType.get_permission_level(current_permission):
            raise ValueError("不能添加权限级别高于或等于自己的成员")
            
        # 检查要添加的用户是否存在
        user = await self.db.execute(
            select(User).filter(User.id == user_id)
        ).scalar_one_or_none()
        
        if not user:
            raise ValueError("用户不存在")
            
        await self.db.execute(
            knowledge_base_users.insert().values(
                knowledge_base_id=self.id,
                user_id=user_id,
                permission=permission,
                created_at=datetime.now()
            )
        )
        await self.db.commit()
        
    async def update_member_permission(
        self,
        user_id: int,
        new_permission: PermissionType,
        current_user_id: int
    ) -> None:
        """更新成员权限
        
        Args:
            user_id: 目标用户ID
            new_permission: 新的权限级别
            current_user_id: 当前操作用户ID
            
        Raises:
            ValueError: 当用户不是成员、是所有者或没有足够权限时
        """
        # 不能修改所有者权限
        if user_id == self.owner_id:
            raise ValueError("不能修改知识库所有者的权限")
            
        # 检查操作权限
        if not await self.check_permission(current_user_id, PermissionType.ADMIN):
            raise ValueError("没有足够的权限执行此操作")
            
        # 获取权限信息
        current_permission = await self.get_effective_permission(current_user_id)
        if not current_permission:
            raise ValueError("没有足够的权限执行此操作")
            
        target_permission = await self.get_member_permission(user_id)
        if not target_permission:
            raise ValueError("目标用户不是知识库成员")
            
        # 不能修改权限级别高于或等于自己的用户
        if PermissionType.get_permission_level(target_permission) >= PermissionType.get_permission_level(current_permission):
            raise ValueError("不能修改权限级别高于或等于自己的用户")
            
        # 不能将用户权限设置为高于自己的级别
        if PermissionType.get_permission_level(new_permission) >= PermissionType.get_permission_level(current_permission):
            raise ValueError("不能将用户权限设置为高于或等于自己的级别")
            
        await self.db.execute(
            knowledge_base_users.update()
            .where(
                and_(
                    knowledge_base_users.c.knowledge_base_id == self.id,
                    knowledge_base_users.c.user_id == user_id
                )
            )
            .values(permission=new_permission)
        )
        await self.db.commit()
        
    async def remove_member(
        self,
        user_id: int,
        current_user_id: int
    ) -> None:
        """移除成员
        
        Args:
            user_id: 要移除的用户ID
            current_user_id: 当前操作用户ID
            
        Raises:
            ValueError: 当用户是所有者或没有足够权限时
        """
        # 不能移除所有者
        if user_id == self.owner_id:
            raise ValueError("不能移除知识库所有者")
            
        # 检查操作权限
        if not await self.check_permission(current_user_id, PermissionType.ADMIN):
            raise ValueError("没有足够的权限执行此操作")
            
        # 获取权限信息
        current_permission = await self.get_effective_permission(current_user_id)
        if not current_permission:
            raise ValueError("没有足够的权限执行此操作")
            
        target_permission = await self.get_member_permission(user_id)
        if not target_permission:
            raise ValueError("目标用户不是知识库成员")
            
        # 不能移除权限级别高于或等于自己的用户
        if PermissionType.get_permission_level(target_permission) >= PermissionType.get_permission_level(current_permission):
            raise ValueError("不能移除权限级别高于或等于自己的用户")
            
        await self.db.execute(
            knowledge_base_users.delete().where(
                and_(
                    knowledge_base_users.c.knowledge_base_id == self.id,
                    knowledge_base_users.c.user_id == user_id
                )
            )
        )
        await self.db.commit()

    async def get_effective_permission(self, user_id: int) -> Optional[PermissionType]:
        """获取用户的有效权限
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[PermissionType]: 用户的有效权限，如果没有权限则返回None
        """
        # 获取用户信息
        user = (await self.db.execute(
            select(User).filter(User.id == user_id)
        )).scalar_one_or_none()
        
        if not user:
            return None
            
        # 如果是所有者，返回所有者权限
        if user_id == self.owner_id:
            return PermissionType.OWNER
            
        # 查询用户权限
        permission = (await self.db.execute(
            select(knowledge_base_users).filter(
                and_(
                    knowledge_base_users.c.knowledge_base_id == self.id,
                    knowledge_base_users.c.user_id == user_id
                )
            )
        )).first()
        
        # 如果有明确的权限记录，返回该权限
        if permission:
            return permission.permission
            
        # 如果是系统管理员但没有明确权限，返回 VIEWER 权限
        if user.is_admin:
            return PermissionType.VIEWER
            
        return None