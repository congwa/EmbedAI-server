"""
知识库主服务类
作为门面模式，整合所有子服务，提供统一的接口
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.knowledge.knowledge_base_core import KnowledgeBaseCoreService
from app.services.knowledge.knowledge_base_training import KnowledgeBaseTrainingService
from app.services.knowledge.knowledge_base_query import KnowledgeBaseQueryService
from app.services.knowledge.knowledge_base_members import KnowledgeBaseMembersService
from app.services.knowledge.knowledge_base_prompt import KnowledgeBasePromptService

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
from app.schemas.identity import UserContext
from app.models.knowledge_base import KnowledgeBase, PermissionType
from app.core.logger import Logger


class KnowledgeBaseService:
    """知识库主服务类 - 门面模式"""
    
    def __init__(self, db: Session):
        self.db = db
        # 初始化所有子服务
        self.core_service = KnowledgeBaseCoreService(db)
        self.training_service = KnowledgeBaseTrainingService(db)
        self.query_service = KnowledgeBaseQueryService(db)
        self.members_service = KnowledgeBaseMembersService(db)
        self.prompt_service = KnowledgeBasePromptService(db)

    # ==================== 核心服务方法 ====================

    async def check_permission(
        self, kb_id: int, user_id: int, required_permission: PermissionType
    ) -> bool:
        """检查用户对知识库的权限"""
        return await self.core_service.check_permission(kb_id, user_id, required_permission)

    async def get_user_permission(
        self, kb_id: int, user_id: int
    ) -> Optional[PermissionType]:
        """获取用户对知识库的权限级别"""
        return await self.core_service.get_user_permission(kb_id, user_id)

    async def create(self, kb: KnowledgeBaseCreate, owner_id: int) -> KnowledgeBase:
        """创建新知识库"""
        return await self.core_service.create(kb, owner_id)

    async def get(self, kb_id: int, user_id: int) -> KnowledgeBase:
        """获取知识库详情"""
        return await self.core_service.get(kb_id, user_id)

    async def update(
        self, kb_id: int, kb: KnowledgeBaseUpdate, user_id: int
    ) -> KnowledgeBase:
        """更新知识库"""
        return await self.core_service.update(kb_id, kb, user_id)

    async def delete(self, kb_id: int, user_id: int) -> None:
        """软删除知识库"""
        return await self.core_service.delete(kb_id, user_id)

    async def get_user_knowledge_bases(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户可访问的所有知识库，并包含成员信息"""
        return await self.core_service.get_user_knowledge_bases(user_id)

    async def check_kb_permission(
        self,
        kb_id: int,
        identity_id: Optional[int],
        required_permission: PermissionType,
    ) -> bool:
        """检查用户对知识库的权限"""
        return await self.core_service.check_kb_permission(kb_id, identity_id, required_permission)

    # ==================== 训练服务方法 ====================

    async def train(self, kb_id: int, user_id: int) -> KnowledgeBase:
        """训练知识库"""
        return await self.training_service.train(kb_id, user_id)

    async def check_training_queue(self) -> Optional[int]:
        """检查训练队列，获取下一个要训练的知识库ID"""
        return await self.training_service.check_training_queue()

    async def get_training_queue_status(self, user_id: int) -> Dict[str, Any]:
        """获取训练队列状态"""
        return await self.training_service.get_training_queue_status(user_id)

    # ==================== 查询服务方法 ====================

    async def query_rag(
        self,
        kb_id: int,
        user_context: UserContext,
        query: str,
        method: str = "semantic_search",
        top_k: int = 5,
        use_rerank: bool = False,
        rerank_mode: str = "weighted_score",
        skip_permission_check: bool = False,
    ) -> dict:
        """RAG查询知识库"""
        return await self.query_service.query_rag(
            kb_id, user_context, query, method, top_k, use_rerank, rerank_mode, skip_permission_check
        )

    async def query(
        self,
        kb_id: int,
        user_context: UserContext,
        query: str,
        top_k: int = 5,
        method: str = "hybrid_search",
        use_rerank: bool = True,
        rerank_mode: str = "weighted_score",
        skip_permission_check: bool = False,
    ) -> dict:
        """查询知识库"""
        return await self.query_service.query(
            kb_id, user_context, query, top_k, method, use_rerank, rerank_mode, skip_permission_check
        )

    # ==================== 成员管理服务方法 ====================

    async def add_user(
        self,
        kb_id: int,
        permission_data: KnowledgeBasePermissionCreate,
        current_user_id: int,
    ) -> None:
        """添加用户到知识库"""
        return await self.members_service.add_user(kb_id, permission_data, current_user_id)

    async def update_user_permission(
        self,
        kb_id: int,
        user_id: int,
        permission_data: KnowledgeBasePermissionUpdate,
        current_user_id: int,
    ) -> None:
        """更新用户的知识库权限"""
        return await self.members_service.update_user_permission(kb_id, user_id, permission_data, current_user_id)

    async def remove_user(self, kb_id: int, user_id: int, current_user_id: int) -> None:
        """从知识库中移除用户"""
        return await self.members_service.remove_user(kb_id, user_id, current_user_id)

    async def get_knowledge_base_users(
        self, kb_id: int, current_user_id: int
    ) -> List[Dict[str, Any]]:
        """获取知识库的所有成员"""
        return await self.members_service.get_knowledge_base_users(kb_id, current_user_id)

    async def get_knowledge_base_members(
        self, kb_id: int, current_user_id: int
    ) -> KnowledgeBaseMemberList:
        """获取知识库成员列表"""
        return await self.members_service.get_knowledge_base_members(kb_id, current_user_id)

    async def add_knowledge_base_member(
        self, kb_id: int, member_data: KnowledgeBaseMemberCreate, current_user_id: int
    ) -> None:
        """添加知识库成员"""
        return await self.members_service.add_knowledge_base_member(kb_id, member_data, current_user_id)

    async def update_knowledge_base_member(
        self,
        kb_id: int,
        user_id: int,
        member_data: KnowledgeBaseMemberUpdate,
        current_user_id: int,
    ) -> None:
        """更新知识库成员权限"""
        return await self.members_service.update_knowledge_base_member(kb_id, user_id, member_data, current_user_id)

    async def remove_knowledge_base_member(
        self, kb_id: int, user_id: int, current_user_id: int
    ) -> None:
        """移除知识库成员"""
        return await self.members_service.remove_knowledge_base_member(kb_id, user_id, current_user_id)

    # ==================== 提示词模板服务方法 ====================

    async def query_with_prompt_template(
        self,
        kb_id: int,
        user_context,
        query: str,
        prompt_template_id: Optional[int] = None,
        method: str = "hybrid_search",
        top_k: int = 5,
        use_rerank: bool = True,
        rerank_mode: str = "weighted_score",
        skip_permission_check: bool = False,
        template_variables: Optional[Dict[str, Any]] = None
    ) -> dict:
        """使用指定提示词模板进行RAG查询"""
        return await self.prompt_service.query_with_prompt_template(
            kb_id, user_context, query, prompt_template_id, method, top_k, 
            use_rerank, rerank_mode, skip_permission_check, template_variables
        )

    async def get_prompt_template_suggestions(
        self,
        kb_id: int,
        user_id: int,
        query_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取适合当前知识库的提示词模板建议"""
        return await self.prompt_service.get_prompt_template_suggestions(kb_id, user_id, query_type)

    async def set_default_prompt_template(
        self,
        kb_id: int,
        user_id: int,
        template_id: Optional[int],
        config: Optional[Dict[str, Any]] = None
    ) -> KnowledgeBase:
        """设置知识库的默认提示词模板"""
        return await self.prompt_service.set_default_prompt_template(kb_id, user_id, template_id, config)

    async def get_prompt_template_config(
        self,
        kb_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """获取知识库的提示词模板配置"""
        return await self.prompt_service.get_prompt_template_config(kb_id, user_id)

    async def update_prompt_template_config(
        self,
        kb_id: int,
        user_id: int,
        config_update: Dict[str, Any]
    ) -> KnowledgeBase:
        """更新知识库的提示词模板配置"""
        return await self.prompt_service.update_prompt_template_config(kb_id, user_id, config_update) 