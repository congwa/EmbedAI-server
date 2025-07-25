from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any, Sequence
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
from app.core.logger import Logger
from app.schemas.identity import UserContext, UserType
from app.models.identity import UserIdentity
from app.rag.training.training_manager import RAGTrainingManager
from app.rag.retrieval.retrieval_service import RetrievalService
from app.rag.retrieval.retrieval_methods import RetrievalMethod
from app.rag.rerank.rerank_type import RerankMode
from app.services.audit import AuditManager
from app.utils.tasks import train_knowledge_base

class KnowledgeBaseService:
    def __init__(self, db: Session):
        self.db = db
        self.session_manager = SessionManager(db)
        self.retrieval_service = RetrievalService(db)
        self.audit_manager = AuditManager(db)

    async def check_permission(
        self,
        kb_id: int,
        user_id: int,
        required_permission: PermissionType
    ) -> bool:
        """检查用户对知识库的权限"""
        kb = (await self.db.execute(
            select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
        )).scalar_one_or_none()
        
        if not kb:
            return False
            
        return await kb.check_permission(self.db, user_id, required_permission)

    async def get_user_permission(
        self,
        kb_id: int,
        user_id: int
    ) -> Optional[PermissionType]:
        """获取用户对知识库的权限级别"""
        kb = (await self.db.execute(
            select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
        )).scalar_one_or_none()
        
        if not kb:
            return None
            
        return await kb.get_member_permission(self.db, user_id)

    async def create(
        self,
        kb: KnowledgeBaseCreate,
        owner_id: int
    ) -> KnowledgeBase:
        """创建新知识库"""
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
        working_dir = f"workspaces/kb_{owner_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        db_kb = KnowledgeBase(
            name=kb.name,
            owner_id=owner_id,
            domain=kb.domain,
            example_queries=kb.example_queries or [],
            entity_types=kb.entity_types or [],
            llm_config=llm_config.model_dump(),
            training_status=TrainingStatus.INIT,
            working_dir=working_dir
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
                created_at=datetime.now()
            )
        )
        
        await self.db.commit()
        await self.db.refresh(db_kb)
        Logger.info(f"Knowledge base '{kb.name}' (ID: {db_kb.id}) created successfully with working directory: {working_dir}")
        return db_kb

    async def train(
        self,
        kb_id: int,
        user_id: int
    ) -> KnowledgeBase:
        """训练知识库"""
        Logger.info(f"开始训练知识库 {kb_id}，请求用户: {user_id}")
        
        # 创建用户上下文
        user_context = UserContext(
            user_type=UserType.OFFICIAL,
            user_id=user_id,
            identity_id=None,
            client_id=None
        )
        
        try:
            # 检查权限
            if not await self.check_permission(kb_id, user_id, PermissionType.EDITOR):
                Logger.warning(f"训练被拒绝: 用户 {user_id} 没有权限训练知识库 {kb_id}")
                
                # 记录审计日志
                await self.audit_manager.log_training(
                    user_context=user_context,
                    kb_id=kb_id,
                    status="permission_denied",
                    error="用户没有足够的权限执行此操作"
                )
                
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="没有足够的权限执行此操作"
                )
                
            kb = (await self.db.execute(
                select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
            )).scalar_one_or_none()
            
            if not kb:
                Logger.error(f"训练失败: 知识库 {kb_id} 不存在")
                
                # 记录审计日志
                await self.audit_manager.log_training(
                    user_context=user_context,
                    kb_id=kb_id,
                    status="not_found",
                    error="知识库不存在"
                )
                
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="知识库不存在"
                )

            # 检查知识库当前状态是否允许训练
            if not kb.can_train:
                Logger.warning(f"训练被拒绝: 知识库 {kb_id} 状态为 {kb.training_status}")
                
                # 记录审计日志
                await self.audit_manager.log_training(
                    user_context=user_context,
                    kb_id=kb_id,
                    status="invalid_status",
                    error=f"当前状态({kb.training_status})不允许训练"
                )
                
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"当前状态({kb.training_status})不允许训练，只有初始状态或训练失败的知识库可以训练"
                )

            # 检查是否已经在队列中
            if kb.training_status == TrainingStatus.QUEUED:
                Logger.warning(f"训练被拒绝: 知识库 {kb_id} 已经在队列中")
                
                # 记录审计日志
                await self.audit_manager.log_training(
                    user_context=user_context,
                    kb_id=kb_id,
                    status="already_queued",
                    error="知识库已在训练队列中"
                )
                
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="知识库已在训练队列中"
                )

            # 获取知识库的所有未删除文档
            documents = (await self.db.execute(
                select(Document).filter(
                    Document.knowledge_base_id == kb_id,
                    Document.is_deleted == False
                )
            )).scalars().all()

            if not documents:
                Logger.error(f"训练失败: 知识库 {kb_id} 没有可用文档")
                
                # 记录审计日志
                await self.audit_manager.log_training(
                    user_context=user_context,
                    kb_id=kb_id,
                    status="no_documents",
                    error="没有可用于训练的文档"
                )
                
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="没有可用于训练的文档"
                )

            Logger.info(f"找到 {len(documents)} 个文档用于训练知识库 {kb_id}")

            # 创建训练管理器
            training_manager = RAGTrainingManager(self.db)

            # 检查是否启用训练队列
            if getattr(settings, 'ENABLE_TRAINING_QUEUE', False):
                # 检查是否有其他知识库正在训练
                training_kb = (await self.db.execute(
                    select(KnowledgeBase).filter(
                        KnowledgeBase.training_status == TrainingStatus.TRAINING
                    )
                )).scalar_one_or_none()

                if training_kb:
                    # 如果有其他知识库在训练，将当前知识库添加到队列
                    Logger.info(f"另一个知识库正在训练，将知识库 {kb_id} 加入队列")
                    await training_manager.update_training_status(kb_id, TrainingStatus.QUEUED)
                    
                    # 记录审计日志
                    await self.audit_manager.log_training(
                        user_context=user_context,
                        kb_id=kb_id,
                        status="queued",
                        document_count=len(documents)
                    )
                    
                    await self.db.refresh(kb)
                    return kb

            # 如果没有其他知识库在训练，直接开始训练
            Logger.info(f"开始立即训练知识库 {kb_id}")
            await training_manager.update_training_status(kb_id, TrainingStatus.TRAINING)
            
            # 记录审计日志
            await self.audit_manager.log_training(
                user_context=user_context,
                kb_id=kb_id,
                status="started",
                document_count=len(documents)
            )
            
            # 启动异步训练任务
            train_knowledge_base(kb_id)
            
            await self.db.refresh(kb)
            return kb
            
        except HTTPException:
            # 直接抛出HTTP异常
            raise
        except Exception as e:
            Logger.error(f"训练知识库 {kb_id} 时发生意外错误: {str(e)}")
            
            # 记录审计日志
            await self.audit_manager.log_training(
                user_context=user_context,
                kb_id=kb_id,
                status="error",
                error=str(e)
            )
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"训练知识库失败: {str(e)}"
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
        skip_permission_check: bool = False
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
                    required_permission=PermissionType.VIEWER
                )
                if not has_permission:
                    Logger.warning(
                        f"查询被拒绝: {user_context.user_type} 用户 {user_context.user_id} "
                        f"没有权限查询知识库 {kb_id}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="没有足够的权限执行此操作"
                    )

            # 获取知识库
            kb = (await self.db.execute(
                select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
            )).scalar_one_or_none()

            if not kb:
                Logger.error(f"查询失败: 知识库 {kb_id} 不存在")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="知识库不存在"
                )

            if kb.training_status != TrainingStatus.TRAINED:
                Logger.warning(
                    f"查询被拒绝: 知识库 {kb_id} 尚未训练完成 "
                    f"(状态: {kb.training_status})"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="知识库尚未训练完成"
                )

            # 创建LLM配置
            llm_config = kb.llm_config
            if isinstance(llm_config, dict):
                from app.schemas.llm import LLMConfig
                llm_config = LLMConfig.model_validate(llm_config)

            # 执行RAG查询
            results = await self.retrieval_service.query(
                knowledge_base=kb,
                query=query,
                llm_config=llm_config,
                method=method,
                top_k=top_k,
                use_rerank=use_rerank,
                rerank_mode=rerank_mode,
                user_id=str(user_context.user_id)
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
                "user_id": user_context.user_id
            }

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
                result_count=len(results)
            )

            return {
                "query": query,
                "results": results,
                "doc_metadata": doc_metadata
            }

        except HTTPException:
            # 直接抛出 HTTP 异常，因为这些是预期的错误
            raise
        except Exception as e:
            import traceback
            error_info = traceback.format_exc()
            Logger.error(
                f"知识库 {kb_id} 查询失败\n"
                f"错误: {str(e)}\n"
                f"堆栈跟踪:\n{error_info}"
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
                error=f"{str(e)}\n{error_info}"
            )
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"查询执行失败: {str(e)}"
            )
            
    async def query(
        self,
        kb_id: int,
        user_context: UserContext,
        query: str,
        top_k: int = 5,
        skip_permission_check: bool = False
    ) -> dict:
        """查询知识库
        
        Args:
            kb_id: 知识库ID
            user_context: 用户上下文信息
            query: 查询内容
            top_k: 返回结果数量
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
            method=RetrievalMethod.HYBRID_SEARCH,  # 默认使用混合搜索
            top_k=top_k,
            use_rerank=True,  # 默认使用重排序
            skip_permission_check=skip_permission_check
        )

    async def get(self, kb_id: int, user_id: int) -> KnowledgeBase:
        """获取知识库详情"""
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
        kb.members = await kb.get_all_members(self.db)
            
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
        user: User = (await self.db.execute(
            select(User).filter(User.id == user_id)
        )).scalar_one_or_none()
        
        # 获取知识库列表
        if user.is_admin:
            knowledge_bases: Sequence[KnowledgeBase] = (await self.db.execute(select(KnowledgeBase))).scalars().all()
        else:
            knowledge_bases: Sequence[KnowledgeBase] = (await self.db.execute(
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
        """获取知识库成员列表"""
        kb = (await self.db.execute(
            select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
        )).scalar_one_or_none()
        
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="知识库不存在"
            )
            
        if not await kb.check_permission(self.db, current_user_id, PermissionType.VIEWER):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有足够的权限执行此操作"
            )
            
        members = await kb.get_all_members(self.db)
        return KnowledgeBaseMemberList(
            members=[KnowledgeBaseMemberInfo(**m) for m in members],
            total=len(members)
        )
        
    async def add_knowledge_base_member(
        self,
        kb_id: int,
        member_data: KnowledgeBaseMemberCreate,
        current_user_id: int
    ) -> None:
        """添加知识库成员"""
        kb = (await self.db.execute(
            select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
        )).scalar_one_or_none()
        
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="知识库不存在"
            )
            
        try:
            await kb.add_member(
                self.db,
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
        """更新知识库成员权限"""
        kb = (await self.db.execute(
            select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
        )).scalar_one_or_none()
        
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="知识库不存在"
            )
            
        try:
            await kb.update_member_permission(
                self.db,
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
        """移除知识库成员"""
        kb = (await self.db.execute(
            select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
        )).scalar_one_or_none()
        
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="知识库不存在"
            )
            
        try:
            await kb.remove_member(
                self.db,
                user_id,
                current_user_id
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
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
                    next_kb_id,
                    TrainingStatus.TRAINING
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
            user = (await self.db.execute(
                select(User).filter(User.id == user_id)
            )).scalar_one_or_none()
            
            if not user or not user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="只有管理员可以查看训练队列状态"
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
                detail=f"获取训练队列状态失败: {str(e)}"
            )

    async def check_kb_permission(
        self,
        kb_id: int,
        identity_id: Optional[int],
        required_permission: PermissionType
    ) -> bool:
        """检查用户对知识库的权限"""
        if not identity_id:
            Logger.warning(f"Permission check failed: No identity provided for knowledge base {kb_id}")
            return False
            
        # 获取用户身份信息
        identity = (await self.db.execute(
            select(UserIdentity).filter(UserIdentity.id == identity_id)
        )).scalar_one_or_none()
        
        if not identity:
            Logger.warning(f"Permission check failed: Identity {identity_id} not found")
            return False
            
        kb = (await self.db.execute(
            select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
        )).scalar_one_or_none()
        
        if not kb:
            Logger.warning(f"Permission check failed: Knowledge base {kb_id} not found")
            return False
            
        # 检查官方用户权限
        if identity.official_user_id:
            return await kb.check_permission(self.db, identity.official_user_id, required_permission)
                
        # 检查第三方用户权限
        if identity.third_party_user_id:
            # 第三方用户对自己的知识库有查看权限
            return True
                    
        Logger.warning(
            f"Permission check failed: Identity {identity_id} "
            f"has no permission for knowledge base {kb_id}"
        )
        return False