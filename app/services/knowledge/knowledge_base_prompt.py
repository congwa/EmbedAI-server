"""
知识库提示词模板服务
负责知识库的提示词模板配置、模板建议和模板管理
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, select
from fastapi import HTTPException, status

from app.models.knowledge_base import KnowledgeBase, PermissionType
from app.services.prompt import PromptService
from app.services.prompt_analytics import PromptAnalyticsService
from app.services.audit import AuditManager
from app.core.logger import Logger


class KnowledgeBasePromptService:
    """知识库提示词模板服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.audit_manager = AuditManager(db)

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
        """使用指定提示词模板进行RAG查询
        
        Args:
            kb_id: 知识库ID
            user_context: 用户上下文信息
            query: 用户查询内容
            prompt_template_id: 提示词模板ID，如果为None则使用知识库默认模板
            method: 检索方法
            top_k: 返回结果数量
            use_rerank: 是否使用重排序
            rerank_mode: 重排序模式
            skip_permission_check: 是否跳过权限检查
            template_variables: 模板变量值
            
        Returns:
            dict: 查询结果，包含渲染后的提示词和RAG响应
            
        Raises:
            HTTPException: 当权限不足、知识库不存在或模板不存在时
        """
        import time
        
        start_time = time.time()
        
        # 记录服务调用开始
        Logger.rag_service_start(
            service="KnowledgeBasePromptService",
            method="query_with_prompt_template",
            kb_id=kb_id,
            user_id=user_context.user_id,
        )
        
        Logger.info(
            f"使用提示词模板进行RAG查询: kb_id={kb_id}, "
            f"template_id={prompt_template_id}, user_id={user_context.user_id}"
        )
        
        try:
            # 检查知识库权限
            if not skip_permission_check:
                from app.services.knowledge.knowledge_base_core import KnowledgeBaseCoreService
                core_service = KnowledgeBaseCoreService(self.db)
                
                has_permission = await core_service.check_kb_permission(
                    kb_id=kb_id,
                    identity_id=user_context.identity_id,
                    required_permission=PermissionType.VIEWER,
                )
                
                if not has_permission:
                    Logger.warning(
                        f"查询被拒绝: 用户 {user_context.user_id} "
                        f"没有权限查询知识库 {kb_id}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="没有足够的权限执行此操作"
                    )
            
            # 获取知识库信息
            kb = (
                await self.db.execute(
                    select(KnowledgeBase).filter(
                        and_(KnowledgeBase.id == kb_id, KnowledgeBase.is_deleted == False)
                    )
                )
            ).scalar_one_or_none()
            
            if not kb:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="知识库不存在"
                )
            
            # 确定使用的提示词模板ID
            template_id_to_use = prompt_template_id
            if not template_id_to_use:
                # 使用知识库默认模板（如果有配置）
                template_id_to_use = getattr(kb, 'default_prompt_template_id', None)
            
            # 执行RAG检索获取上下文
            from app.services.knowledge.knowledge_base_query import KnowledgeBaseQueryService
            query_service = KnowledgeBaseQueryService(self.db)
            
            rag_result = await query_service.query_rag(
                kb_id=kb_id,
                user_context=user_context,
                query=query,
                method=method,
                top_k=top_k,
                use_rerank=use_rerank,
                rerank_mode=rerank_mode,
                skip_permission_check=True  # 已经检查过权限
            )
            
            # 提取检索到的上下文
            context_text = ""
            if "results" in rag_result and rag_result["results"]:
                context_chunks = []
                for result in rag_result["results"]:
                    if "content" in result:
                        context_chunks.append(result["content"])
                context_text = "\n\n".join(context_chunks)
            
            # 如果指定了提示词模板，进行模板渲染
            rendered_prompt = None
            template_info = None
            
            if template_id_to_use:
                try:
                    prompt_service = PromptService(self.db)
                    
                    # 准备模板变量
                    template_vars = {
                        "query": query,
                        "context": context_text,
                        "kb_name": kb.name,
                        "kb_description": kb.description or "",
                    }
                    
                    # 合并用户提供的变量
                    if template_variables:
                        template_vars.update(template_variables)
                    
                    # 渲染模板
                    render_result = await prompt_service.render_template(
                        template_id_to_use,
                        template_vars,
                        user_context.user_id
                    )
                    
                    rendered_prompt = render_result.rendered_content
                    
                    # 获取模板信息
                    template = await prompt_service.get_template(
                        template_id_to_use, 
                        user_context.user_id
                    )
                    
                    template_info = {
                        "id": template.id,
                        "name": template.name,
                        "version": "current",  # 可以扩展为具体版本
                        "variables_used": render_result.variables_used
                    }
                    
                    # 记录提示词使用统计
                    analytics_service = PromptAnalyticsService(self.db)
                    await analytics_service.log_usage(
                        template_id=template_id_to_use,
                        user_id=user_context.user_id,
                        kb_id=kb_id,
                        query=query,
                        variables_used=template_vars,
                        rendered_content=rendered_prompt,
                        execution_time=time.time() - start_time,
                        success=True
                    )
                    
                    Logger.info(f"提示词模板渲染成功: template_id={template_id_to_use}")
                    
                except Exception as e:
                    Logger.error(f"提示词模板处理失败: {str(e)}")
                    
                    # 记录失败统计
                    if template_id_to_use:
                        try:
                            analytics_service = PromptAnalyticsService(self.db)
                            await analytics_service.log_usage(
                                template_id=template_id_to_use,
                                user_id=user_context.user_id,
                                kb_id=kb_id,
                                query=query,
                                variables_used=template_variables or {},
                                execution_time=time.time() - start_time,
                                success=False,
                                error_message=str(e)
                            )
                        except:
                            pass  # 避免统计记录失败影响主流程
                    
                    # 如果模板处理失败，使用默认提示词
                    rendered_prompt = self._get_default_prompt(query, context_text)
                    template_info = {
                        "id": None,
                        "name": "默认模板",
                        "version": "default",
                        "error": str(e)
                    }
            else:
                # 没有指定模板，使用默认提示词
                rendered_prompt = self._get_default_prompt(query, context_text)
                template_info = {
                    "id": None,
                    "name": "默认模板",
                    "version": "default"
                }
            
            # 构建最终响应
            response = {
                "query": query,
                "kb_id": kb_id,
                "kb_name": kb.name,
                "template_info": template_info,
                "rendered_prompt": rendered_prompt,
                "context": context_text,
                "rag_results": rag_result.get("results", []),
                "retrieval_info": {
                    "method": method,
                    "top_k": top_k,
                    "use_rerank": use_rerank,
                    "total_results": len(rag_result.get("results", []))
                },
                "execution_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            }
            
            Logger.info(
                f"提示词模板查询完成: kb_id={kb_id}, "
                f"template_id={template_id_to_use}, "
                f"execution_time={response['execution_time']:.3f}s"
            )
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            Logger.error(f"提示词模板查询失败: {str(e)}")
            
            # 记录失败统计
            if prompt_template_id:
                try:
                    analytics_service = PromptAnalyticsService(self.db)
                    await analytics_service.log_usage(
                        template_id=prompt_template_id,
                        user_id=user_context.user_id,
                        kb_id=kb_id,
                        query=query,
                        variables_used=template_variables or {},
                        execution_time=time.time() - start_time,
                        success=False,
                        error_message=str(e)
                    )
                except:
                    pass  # 避免统计记录失败影响主流程
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"查询失败: {str(e)}"
            )
    
    def _get_default_prompt(self, query: str, context: str) -> str:
        """获取默认提示词
        
        Args:
            query: 用户查询
            context: 检索到的上下文
            
        Returns:
            str: 默认提示词内容
        """
        return f"""你是一个专业的AI助手，基于以下上下文信息回答用户问题。

上下文信息：
{context}

用户问题：
{query}

请基于上下文信息给出准确、有用的回答。如果上下文信息不足以回答问题，请明确说明。"""

    async def get_prompt_template_suggestions(
        self,
        kb_id: int,
        user_id: int,
        query_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取适合当前知识库的提示词模板建议
        
        Args:
            kb_id: 知识库ID
            user_id: 用户ID
            query_type: 查询类型（可选）
            
        Returns:
            List[Dict[str, Any]]: 推荐的模板列表
        """
        try:
            Logger.info(f"获取知识库 {kb_id} 的提示词模板建议")
            
            # 检查权限
            from app.services.knowledge.knowledge_base_core import KnowledgeBaseCoreService
            core_service = KnowledgeBaseCoreService(self.db)
            
            if not await core_service.check_permission(kb_id, user_id, PermissionType.VIEWER):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="没有足够的权限执行此操作"
                )
            
            prompt_service = PromptService(self.db)
            analytics_service = PromptAnalyticsService(self.db)
            
            # 获取用户可访问的模板
            templates, _ = await prompt_service.list_templates(
                user_id=user_id,
                page=1,
                page_size=50
            )
            
            # 获取在此知识库中使用最多的模板
            usage_stats = await analytics_service.get_usage_stats(
                kb_id=kb_id,
                include_trend=False
            )
            
            # 构建推荐列表
            suggestions = []
            
            # 添加使用统计信息
            usage_map = {stat.template_id: stat for stat in usage_stats}
            
            for template in templates:
                suggestion = {
                    "id": template.id,
                    "name": template.name,
                    "description": template.description,
                    "tags": template.tags or [],
                    "is_system": template.is_system,
                    "usage_in_kb": 0,
                    "success_rate": 0.0,
                    "avg_response_quality": None,
                    "recommendation_score": 0.0
                }
                
                # 添加使用统计
                if template.id in usage_map:
                    stat = usage_map[template.id]
                    suggestion.update({
                        "usage_in_kb": stat.total_usage,
                        "success_rate": stat.success_rate,
                        "avg_response_quality": stat.avg_response_quality
                    })
                
                # 计算推荐分数（基于使用量、成功率、质量等）
                score = 0.0
                if suggestion["usage_in_kb"] > 0:
                    score += min(suggestion["usage_in_kb"] * 0.1, 5.0)  # 使用量权重
                    score += suggestion["success_rate"] * 3.0  # 成功率权重
                    if suggestion["avg_response_quality"]:
                        score += suggestion["avg_response_quality"] * 2.0  # 质量权重
                
                # 系统模板额外加分
                if suggestion["is_system"]:
                    score += 1.0
                
                suggestion["recommendation_score"] = score
                suggestions.append(suggestion)
            
            # 按推荐分数排序
            suggestions.sort(key=lambda x: x["recommendation_score"], reverse=True)
            
            # 返回前10个推荐
            return suggestions[:10]
            
        except HTTPException:
            raise
        except Exception as e:
            Logger.error(f"获取提示词模板建议失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取模板建议失败: {str(e)}"
            )

    async def set_default_prompt_template(
        self,
        kb_id: int,
        user_id: int,
        template_id: Optional[int],
        config: Optional[Dict[str, Any]] = None
    ) -> KnowledgeBase:
        """设置知识库的默认提示词模板
        
        Args:
            kb_id: 知识库ID
            user_id: 用户ID
            template_id: 提示词模板ID，None表示清除默认模板
            config: 提示词模板配置
            
        Returns:
            KnowledgeBase: 更新后的知识库对象
        """
        try:
            Logger.info(f"用户 {user_id} 为知识库 {kb_id} 设置默认提示词模板: {template_id}")
            
            # 检查权限（需要编辑权限）
            from app.services.knowledge.knowledge_base_core import KnowledgeBaseCoreService
            core_service = KnowledgeBaseCoreService(self.db)
            
            if not await core_service.check_permission(kb_id, user_id, PermissionType.EDITOR):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="没有足够的权限执行此操作"
                )
            
            # 获取知识库
            kb = (
                await self.db.execute(
                    select(KnowledgeBase).filter(
                        and_(KnowledgeBase.id == kb_id, KnowledgeBase.is_deleted == False)
                    )
                )
            ).scalar_one_or_none()
            
            if not kb:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="知识库不存在"
                )
            
            # 如果指定了模板ID，验证模板是否存在且用户有权限访问
            if template_id:
                prompt_service = PromptService(self.db)
                try:
                    await prompt_service.get_template(template_id, user_id)
                except HTTPException as e:
                    if e.status_code == 404:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="指定的提示词模板不存在"
                        )
                    elif e.status_code == 403:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="没有权限访问指定的提示词模板"
                        )
                    else:
                        raise
            
            # 设置默认模板
            await kb.set_default_prompt_template(self.db, template_id, config)
            
            # 记录审计日志
            await self.audit_manager.log_action(
                user_id=user_id,
                action="set_default_prompt_template",
                resource_type="knowledge_base",
                resource_id=kb_id,
                details={
                    "template_id": template_id,
                    "config": config
                }
            )
            
            Logger.info(f"知识库 {kb_id} 默认提示词模板设置成功")
            return kb
            
        except HTTPException:
            raise
        except Exception as e:
            Logger.error(f"设置默认提示词模板失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"设置默认模板失败: {str(e)}"
            )

    async def get_prompt_template_config(
        self,
        kb_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """获取知识库的提示词模板配置
        
        Args:
            kb_id: 知识库ID
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 提示词模板配置信息
        """
        try:
            Logger.info(f"用户 {user_id} 获取知识库 {kb_id} 的提示词模板配置")
            
            # 检查权限
            from app.services.knowledge.knowledge_base_core import KnowledgeBaseCoreService
            core_service = KnowledgeBaseCoreService(self.db)
            
            if not await core_service.check_permission(kb_id, user_id, PermissionType.VIEWER):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="没有足够的权限执行此操作"
                )
            
            # 获取知识库
            kb = (
                await self.db.execute(
                    select(KnowledgeBase).filter(
                        and_(KnowledgeBase.id == kb_id, KnowledgeBase.is_deleted == False)
                    )
                )
            ).scalar_one_or_none()
            
            if not kb:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="知识库不存在"
                )
            
            # 构建配置信息
            config = {
                "kb_id": kb_id,
                "kb_name": kb.name,
                "default_template_id": kb.default_prompt_template_id,
                "template_config": kb.get_prompt_template_config(),
                "selection_strategy": kb.get_template_selection_strategy(),
                "variable_mapping": kb.get_template_variable_mapping(),
                "supports_dynamic_selection": kb.supports_dynamic_template_selection()
            }
            
            # 如果有默认模板，获取模板信息
            if kb.default_prompt_template_id:
                try:
                    prompt_service = PromptService(self.db)
                    template = await prompt_service.get_template(
                        kb.default_prompt_template_id, 
                        user_id
                    )
                    config["default_template_info"] = {
                        "id": template.id,
                        "name": template.name,
                        "description": template.description,
                        "variables": template.variables or []
                    }
                except:
                    # 如果获取模板信息失败，不影响主流程
                    config["default_template_info"] = None
            
            # 获取推荐模板
            recommendations = await self.get_prompt_template_suggestions(kb_id, user_id)
            config["recommended_templates"] = recommendations
            
            return config
            
        except HTTPException:
            raise
        except Exception as e:
            Logger.error(f"获取提示词模板配置失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取模板配置失败: {str(e)}"
            )

    async def update_prompt_template_config(
        self,
        kb_id: int,
        user_id: int,
        config_update: Dict[str, Any]
    ) -> KnowledgeBase:
        """更新知识库的提示词模板配置
        
        Args:
            kb_id: 知识库ID
            user_id: 用户ID
            config_update: 配置更新数据
            
        Returns:
            KnowledgeBase: 更新后的知识库对象
        """
        try:
            Logger.info(f"用户 {user_id} 更新知识库 {kb_id} 的提示词模板配置")
            
            # 检查权限
            from app.services.knowledge.knowledge_base_core import KnowledgeBaseCoreService
            core_service = KnowledgeBaseCoreService(self.db)
            
            if not await core_service.check_permission(kb_id, user_id, PermissionType.EDITOR):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="没有足够的权限执行此操作"
                )
            
            # 获取知识库
            kb = (
                await self.db.execute(
                    select(KnowledgeBase).filter(
                        and_(KnowledgeBase.id == kb_id, KnowledgeBase.is_deleted == False)
                    )
                )
            ).scalar_one_or_none()
            
            if not kb:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="知识库不存在"
                )
            
            # 获取当前配置
            current_config = kb.get_prompt_template_config()
            
            # 合并配置更新
            updated_config = {**current_config, **config_update}
            
            # 验证配置
            self._validate_prompt_template_config(updated_config)
            
            # 更新配置
            kb.prompt_template_config = updated_config
            kb.updated_at = datetime.now()
            
            self.db.add(kb)
            await self.db.commit()
            
            # 记录审计日志
            await self.audit_manager.log_action(
                user_id=user_id,
                action="update_prompt_template_config",
                resource_type="knowledge_base",
                resource_id=kb_id,
                details={
                    "config_update": config_update,
                    "updated_config": updated_config
                }
            )
            
            Logger.info(f"知识库 {kb_id} 提示词模板配置更新成功")
            return kb
            
        except HTTPException:
            raise
        except Exception as e:
            Logger.error(f"更新提示词模板配置失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新模板配置失败: {str(e)}"
            )

    def _validate_prompt_template_config(self, config: Dict[str, Any]) -> None:
        """验证提示词模板配置
        
        Args:
            config: 配置数据
            
        Raises:
            HTTPException: 当配置无效时
        """
        # 验证选择策略
        valid_strategies = ["default", "dynamic", "user_choice"]
        strategy = config.get("selection_strategy", "default")
        if strategy not in valid_strategies:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的模板选择策略: {strategy}，支持的策略: {valid_strategies}"
            )
        
        # 验证变量映射
        variable_mapping = config.get("variable_mapping", {})
        if not isinstance(variable_mapping, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="变量映射必须是字典格式"
            )
        
        # 验证推荐配置
        recommendations = config.get("recommendations", {})
        if not isinstance(recommendations, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="推荐配置必须是字典格式"
            )
        
        # 验证推荐模板ID列表
        for query_type, template_ids in recommendations.items():
            if not isinstance(template_ids, list):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"推荐模板ID列表必须是数组格式: {query_type}"
                )
            
            for template_id in template_ids:
                if not isinstance(template_id, int) or template_id <= 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"无效的模板ID: {template_id}"
                    ) 