"""
知识库提示词模板相关API
包含提示词模板配置、查询等操作
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import get_db
from app.services.auth import get_current_user
from app.services.knowledge_base import KnowledgeBaseService
from app.core.response_utils import success_response
from app.models.user import User
from app.core.decorators import require_knowledge_base_permission
from app.models.enums import PermissionType
from app.core.logger import Logger
from app.core.exceptions_new import SystemError, BusinessError

router = APIRouter()


@router.get("/{kb_id}/prompt-template-config")
@require_knowledge_base_permission(PermissionType.VIEWER)
async def get_prompt_template_config(
    kb_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取知识库的提示词模板配置
    
    Args:
        kb_id: 知识库ID
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        APIResponse: 包含提示词模板配置的响应
    """
    try:
        Logger.info(f"用户 {current_user.id} 获取知识库 {kb_id} 的提示词模板配置")
        
        kb_service = KnowledgeBaseService(db)
        config = await kb_service.get_prompt_template_config(kb_id, current_user.id)
        
        return success_response(data=config)
        
    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"获取提示词模板配置失败: {str(e)}")
        raise SystemError("获取配置失败", original_exception=e)


@router.put("/{kb_id}/prompt-template-config/default")
@require_knowledge_base_permission(PermissionType.EDITOR)
async def set_default_prompt_template(
    kb_id: int,
    request_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """设置知识库的默认提示词模板
    
    Args:
        kb_id: 知识库ID
        request_data: 请求数据，包含template_id和config
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        APIResponse: 成功响应
    """
    try:
        Logger.info(f"用户 {current_user.id} 为知识库 {kb_id} 设置默认提示词模板")
        
        template_id = request_data.get("template_id")
        config = request_data.get("config", {})
        
        kb_service = KnowledgeBaseService(db)
        kb = await kb_service.set_default_prompt_template(
            kb_id, current_user.id, template_id, config
        )
        
        return success_response(
            data={
                "kb_id": kb.id,
                "default_template_id": kb.default_prompt_template_id,
                "config": kb.get_prompt_template_config()
            },
            message="默认提示词模板设置成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"设置默认提示词模板失败: {str(e)}")
        raise SystemError("设置默认模板失败", original_exception=e)


@router.put("/{kb_id}/prompt-template-config")
@require_knowledge_base_permission(PermissionType.EDITOR)
async def update_prompt_template_config(
    kb_id: int,
    config_update: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新知识库的提示词模板配置
    
    Args:
        kb_id: 知识库ID
        config_update: 配置更新数据
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        APIResponse: 成功响应
    """
    try:
        Logger.info(f"用户 {current_user.id} 更新知识库 {kb_id} 的提示词模板配置")
        
        kb_service = KnowledgeBaseService(db)
        kb = await kb_service.update_prompt_template_config(
            kb_id, current_user.id, config_update
        )
        
        return success_response(
            data={
                "kb_id": kb.id,
                "updated_config": kb.get_prompt_template_config()
            },
            message="提示词模板配置更新成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"更新提示词模板配置失败: {str(e)}")
        raise SystemError("更新配置失败", original_exception=e)


@router.post("/{kb_id}/query-with-prompt")
@require_knowledge_base_permission(PermissionType.VIEWER)
async def query_with_prompt_template(
    kb_id: int,
    request_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """使用指定提示词模板查询知识库
    
    Args:
        kb_id: 知识库ID
        request_data: 查询请求数据
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        APIResponse: 查询结果响应
    """
    try:
        Logger.info(f"用户 {current_user.id} 使用提示词模板查询知识库 {kb_id}")
        
        # 提取请求参数
        query = request_data.get("query")
        if not query:
            raise BusinessError("查询内容不能为空")
        
        prompt_template_id = request_data.get("prompt_template_id")
        template_variables = request_data.get("template_variables", {})
        method = request_data.get("method", "hybrid_search")
        top_k = request_data.get("top_k", 5)
        use_rerank = request_data.get("use_rerank", True)
        
        # 构建用户上下文
        from app.schemas.identity import UserContext, UserType
        user_context = UserContext(
            user_id=current_user.id,
            user_type=UserType.OFFICIAL,
            identity_id=current_user.id  # 对于官方用户，identity_id就是user_id
        )
        
        kb_service = KnowledgeBaseService(db)
        result = await kb_service.query_with_prompt_template(
            kb_id=kb_id,
            user_context=user_context,
            query=query,
            prompt_template_id=prompt_template_id,
            method=method,
            top_k=top_k,
            use_rerank=use_rerank,
            template_variables=template_variables
        )
        
        return success_response(data=result)
        
    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"使用提示词模板查询失败: {str(e)}")
        raise SystemError("查询失败", original_exception=e)


@router.get("/{kb_id}/prompt-template-suggestions")
@require_knowledge_base_permission(PermissionType.VIEWER)
async def get_prompt_template_suggestions(
    kb_id: int,
    query_type: str = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取知识库的提示词模板建议
    
    Args:
        kb_id: 知识库ID
        query_type: 查询类型（可选）
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        APIResponse: 包含推荐模板列表的响应
    """
    try:
        Logger.info(f"用户 {current_user.id} 获取知识库 {kb_id} 的提示词模板建议")
        
        kb_service = KnowledgeBaseService(db)
        suggestions = await kb_service.get_prompt_template_suggestions(
            kb_id, current_user.id, query_type
        )
        
        return success_response(data=suggestions)
        
    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"获取提示词模板建议失败: {str(e)}")
        raise SystemError("获取建议失败", original_exception=e) 