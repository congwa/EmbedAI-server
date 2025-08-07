from sqlalchemy import Column, Integer, String, ForeignKey, JSON, ARRAY, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Session

from .database import Base
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.schemas.base import CustomBaseModel
from sqlalchemy.sql import select, and_
from .associations import knowledge_base_users
from .enums import PermissionType, TrainingStatus
from app.models.user import User
from app.core.logger import Logger
class KnowledgeBase(Base):
    """知识库模型
    
    用于存储知识库的基本信息、配置和训练状态
    支持多用户协作和权限管理
    """
    __tablename__ = "knowledge_bases"
    __table_args__ = {'comment': '知识库表，存储知识库基本信息和训练状态'}

    id = Column(Integer, primary_key=True, index=True, comment='知识库ID')
    name = Column(String, nullable=False, comment='知识库名称')
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment='所有者用户ID')
    domain = Column(String, nullable=False, comment='知识库领域')
    example_queries = Column(JSON, nullable=False, comment='示例查询列表，用于指导用户如何使用知识库')
    entity_types = Column(JSON, nullable=False, comment='实体类型列表，用于定义知识库中的实体类型')
    llm_config = Column(JSON, nullable=True, comment='LLM配置，包含模型和嵌入等配置信息')
    working_dir = Column(String, nullable=True, comment='工作目录，用于存储知识库相关的文件')
    
    # RAG相关字段
    indexing_technique = Column(String, nullable=False, default="high_quality", comment='索引技术（high_quality或economy）')
    embedding_model = Column(String, nullable=True, comment='嵌入模型名称')
    embedding_model_provider = Column(String, nullable=True, comment='嵌入模型提供商')
    vector_store_type = Column(String, nullable=True, comment='向量存储类型')
    
    # 提示词模板相关字段
    default_prompt_template_id = Column(Integer, ForeignKey("prompt_templates.id", ondelete="SET NULL"), nullable=True, comment='默认提示词模板ID')
    prompt_template_config = Column(JSON, nullable=True, comment='提示词模板配置，包含模板选择策略和变量映射')
    
    # 时间字段
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    # 训练相关字段
    training_status = Column(Enum(TrainingStatus), nullable=False, default=TrainingStatus.INIT, comment='训练状态')
    training_started_at = Column(DateTime, nullable=True, comment='训练开始时间')
    training_finished_at = Column(DateTime, nullable=True, comment='训练完成时间')
    training_error = Column(String, nullable=True, comment='训练错误信息')
    queued_at = Column(DateTime, nullable=True, comment='进入训练队列的时间')
    
    # 关系定义
    owner = relationship("User", back_populates="owned_knowledge_bases", foreign_keys=[owner_id], passive_deletes=True)
    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan", passive_deletes=True)
    users = relationship(
        "User", 
        secondary=knowledge_base_users,
        back_populates="knowledge_bases",
        passive_deletes=True
    )
    chats = relationship("Chat", back_populates="knowledge_base", cascade="all, delete-orphan")
    default_prompt_template = relationship("PromptTemplate", foreign_keys=[default_prompt_template_id])
    
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
        
    async def get_member_permission(self, db: Session, user_id: int) -> Optional[PermissionType]:
        """获取用户在知识库中的权限
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            Optional[PermissionType]: 用户权限，如果不是成员则返回None
        """
        result = await db.execute(
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
        db: Session,
        user_id: int,
        required_permission: PermissionType
    ) -> bool:
        """检查用户对知识库的权限
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            required_permission: 所需的权限级别
            
        Returns:
            bool: 是否有权限
        """
        # 管理员用户拥有所有权限
        user = (await db.execute(
            select(User).filter(User.id == user_id)
        )).scalar_one_or_none()
        
        if user and user.is_admin:
            return True
            
        # 查询用户权限
        permission = (await db.execute(
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
        
    async def get_all_members(self, db: Session) -> List[Dict[str, Any]]:
        """获取所有成员信息
        
        Args:
            db: 数据库会话
            
        Returns:
            List[Dict[str, Any]]: 成员列表
        """
        result = await db.execute(
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
        db: Session,
        user_id: int,
        permission: PermissionType,
        current_user_id: int
    ) -> None:
        """添加成员
        
        Args:
            db: 数据库会话
            user_id: 要添加的用户ID
            permission: 权限级别
            current_user_id: 当前操作用户ID
            
        Raises:
            ValueError: 当用户已是成员或没有足够权限时
        """
        try:
            # 检查是否已是成员
            if await self.get_member_permission(db, user_id):
                raise ValueError("用户已是知识库成员")
                
            # 检查操作权限
            if not await self.check_permission(db, current_user_id, PermissionType.ADMIN):
                raise ValueError("没有足够的权限执行此操作")
                
            # 获取当前用户有效权限
            current_permission = await self.get_effective_permission(db, current_user_id)
            if not current_permission:
                raise ValueError("没有足够的权限执行此操作")
                
            # 不能添加权限级别高于或等于自己的成员
            if PermissionType.get_permission_level(permission) >= PermissionType.get_permission_level(current_permission):
                raise ValueError("不能添加权限级别高于或等于自己的成员")
                
            # 检查要添加的用户是否存在
            user = (await db.execute(
                select(User).filter(User.id == user_id)
            )).scalar_one_or_none()
            
            if not user:
                raise ValueError("用户不存在")
                
            await db.execute(
                knowledge_base_users.insert().values(
                    knowledge_base_id=self.id,
                    user_id=user_id,
                    permission=permission,
                    created_at=datetime.now()
                )
            )
            await db.commit()
        except Exception as e:
            import traceback
            error_info = traceback.format_exc()
            Logger.error(
                f"Failed to add member (user_id: {user_id}) to knowledge base {self.id}\n"
                f"Error: {str(e)}\n"
                f"Traceback:\n{error_info}"
            )
            raise
        
    async def update_member_permission(
        self,
        db: Session,
        user_id: int,
        new_permission: PermissionType,
        current_user_id: int
    ) -> None:
        """更新成员权限
        
        Args:
            db: 数据库会话
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
        if not await self.check_permission(db, current_user_id, PermissionType.ADMIN):
            raise ValueError("没有足够的权限执行此操作")
            
        # 获取权限信息
        current_permission = await self.get_effective_permission(db, current_user_id)
        if not current_permission:
            raise ValueError("没有足够的权限执行此操作")
            
        target_permission = await self.get_member_permission(db, user_id)
        if not target_permission:
            raise ValueError("目标用户不是知识库成员")
            
        # 不能修改权限级别高于或等于自己的用户
        if PermissionType.get_permission_level(target_permission) >= PermissionType.get_permission_level(current_permission):
            raise ValueError("不能修改权限级别高于或等于自己的用户")
            
        # 不能将用户权限设置为高于自己的级别
        if PermissionType.get_permission_level(new_permission) >= PermissionType.get_permission_level(current_permission):
            raise ValueError("不能将用户权限设置为高于或等于自己的级别")
            
        await db.execute(
            knowledge_base_users.update()
            .where(
                and_(
                    knowledge_base_users.c.knowledge_base_id == self.id,
                    knowledge_base_users.c.user_id == user_id
                )
            )
            .values(permission=new_permission)
        )
        await db.commit()
        
    async def remove_member(
        self,
        db: Session,
        user_id: int,
        current_user_id: int
    ) -> None:
        """移除成员
        
        Args:
            db: 数据库会话
            user_id: 要移除的用户ID
            current_user_id: 当前操作用户ID
            
        Raises:
            ValueError: 当用户是所有者或没有足够权限时
        """
        # 不能移除所有者
        if user_id == self.owner_id:
            raise ValueError("不能移除知识库所有者")
            
        # 检查操作权限
        if not await self.check_permission(db, current_user_id, PermissionType.ADMIN):
            raise ValueError("没有足够的权限执行此操作")
            
        # 获取权限信息
        current_permission = await self.get_effective_permission(db, current_user_id)
        if not current_permission:
            raise ValueError("没有足够的权限执行此操作")
            
        target_permission = await self.get_member_permission(db, user_id)
        if not target_permission:
            raise ValueError("目标用户不是知识库成员")
            
        # 不能移除权限级别高于或等于自己的用户
        if PermissionType.get_permission_level(target_permission) >= PermissionType.get_permission_level(current_permission):
            raise ValueError("不能移除权限级别高于或等于自己的用户")
            
        await db.execute(
            knowledge_base_users.delete().where(
                and_(
                    knowledge_base_users.c.knowledge_base_id == self.id,
                    knowledge_base_users.c.user_id == user_id
                )
            )
        )
        await db.commit()

    async def get_effective_permission(self, db: Session, user_id: int) -> Optional[PermissionType]:
        """获取用户的有效权限
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            Optional[PermissionType]: 用户的有效权限，如果没有权限则返回None
        """
        # 获取用户信息
        user = (await db.execute(
            select(User).filter(User.id == user_id)
        )).scalar_one_or_none()
        
        if not user:
            return None
            
        # 如果是所有者，返回所有者权限
        if user_id == self.owner_id:
            return PermissionType.OWNER
            
        # 查询用户权限
        permission = (await db.execute(
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
            
        return None    as
ync def set_default_prompt_template(
        self, 
        db: Session, 
        template_id: Optional[int], 
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """设置默认提示词模板
        
        Args:
            db: 数据库会话
            template_id: 提示词模板ID，None表示清除默认模板
            config: 提示词模板配置
        """
        self.default_prompt_template_id = template_id
        self.prompt_template_config = config or {}
        self.updated_at = datetime.now()
        
        db.add(self)
        await db.commit()
        
        Logger.info(f"知识库 {self.id} 设置默认提示词模板: {template_id}")
    
    def get_prompt_template_config(self) -> Dict[str, Any]:
        """获取提示词模板配置
        
        Returns:
            Dict[str, Any]: 提示词模板配置
        """
        return self.prompt_template_config or {}
    
    def get_template_variable_mapping(self) -> Dict[str, str]:
        """获取模板变量映射配置
        
        Returns:
            Dict[str, str]: 变量映射配置
        """
        config = self.get_prompt_template_config()
        return config.get("variable_mapping", {})
    
    def get_template_selection_strategy(self) -> str:
        """获取模板选择策略
        
        Returns:
            str: 模板选择策略 (default, dynamic, user_choice)
        """
        config = self.get_prompt_template_config()
        return config.get("selection_strategy", "default")
    
    async def get_recommended_templates(
        self, 
        db: Session, 
        query_type: Optional[str] = None
    ) -> List[int]:
        """获取推荐的提示词模板ID列表
        
        Args:
            db: 数据库会话
            query_type: 查询类型
            
        Returns:
            List[int]: 推荐的模板ID列表
        """
        config = self.get_prompt_template_config()
        recommendations = config.get("recommendations", {})
        
        if query_type and query_type in recommendations:
            return recommendations[query_type]
        
        # 返回默认推荐
        return recommendations.get("default", [])
    
    def supports_dynamic_template_selection(self) -> bool:
        """检查是否支持动态模板选择
        
        Returns:
            bool: 是否支持动态选择
        """
        strategy = self.get_template_selection_strategy()
        return strategy in ["dynamic", "user_choice"]
    
    def to_dict_with_prompt_config(self) -> Dict[str, Any]:
        """转换为字典，包含提示词配置信息
        
        Returns:
            Dict[str, Any]: 包含提示词配置的字典
        """
        result = self.to_dict()
        
        # 添加提示词模板相关信息
        result.update({
            "default_prompt_template_id": self.default_prompt_template_id,
            "prompt_template_config": self.get_prompt_template_config(),
            "supports_dynamic_templates": self.supports_dynamic_template_selection()
        })
        
        return result