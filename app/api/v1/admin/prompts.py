"""提示词管理API接口"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.prompt import PromptService, PromptCategoryService
from app.services.prompt_analytics import PromptAnalyticsService
from app.schemas.prompt import (
    PromptTemplateCreate, PromptTemplateUpdate, PromptTemplateResponse,
    PromptTemplateList, PromptTemplateRenderRequest, PromptTemplateRenderResponse,
    PromptTemplateValidateRequest, PromptTemplateValidateResponse,
    PromptCategoryCreate, PromptCategoryUpdate, PromptCategoryResponse,
    PromptUsageStats, PromptUsageLogResponse
)
from app.core.logger import Logger

router = APIRouter()


@router.post("/templates", response_model=PromptTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: PromptTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建提示词模板
    
    创建新的提示词模板，支持变量定义和分类管理
    """
    try:
        Logger.info(f"用户 {current_user.id} 创建提示词模板: {template_data.name}")
        
        prompt_service = PromptService(db)
        template = await prompt_service.create_template(template_data, current_user.id)
        
        # 构建响应数据
        response = PromptTemplateResponse(
            id=template.id,
            name=template.name,
            description=template.description,
            category_id=template.category_id,
            content=template.content,
            variables=template.variables or [],
            tags=template.tags or [],
            is_system=template.is_system,
            is_active=template.is_active,
            owner_id=template.owner_id,
            usage_count=template.usage_count,
            last_used_at=template.last_used_at,
            created_at=template.created_at,
            updated_at=template.updated_at,
            category_name=template.category.name if template.category else None,
            owner_email=template.owner.email if template.owner else None
        )
        
        return response
        
    except Exception as e:
        Logger.error(f"创建提示词模板失败: {str(e)}")
        raise


@router.get("/templates", response_model=PromptTemplateList)
async def list_templates(
    category_id: Optional[int] = Query(None, description="分类ID筛选"),
    tags: Optional[List[str]] = Query(None, description="标签筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    is_system: Optional[bool] = Query(None, description="是否系统模板"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页大小"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取提示词模板列表
    
    支持分页、筛选和搜索功能
    """
    try:
        Logger.info(f"用户 {current_user.id} 获取提示词模板列表")
        
        prompt_service = PromptService(db)
        templates, total = await prompt_service.list_templates(
            user_id=current_user.id,
            category_id=category_id,
            tags=tags,
            search=search,
            is_system=is_system,
            page=page,
            page_size=page_size
        )
        
        # 构建响应数据
        template_responses = []
        for template in templates:
            response = PromptTemplateResponse(
                id=template.id,
                name=template.name,
                description=template.description,
                category_id=template.category_id,
                content=template.content,
                variables=template.variables or [],
                tags=template.tags or [],
                is_system=template.is_system,
                is_active=template.is_active,
                owner_id=template.owner_id,
                usage_count=template.usage_count,
                last_used_at=template.last_used_at,
                created_at=template.created_at,
                updated_at=template.updated_at,
                category_name=template.category.name if template.category else None,
                owner_email=template.owner.email if template.owner else None
            )
            template_responses.append(response)
        
        return PromptTemplateList(
            templates=template_responses,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        Logger.error(f"获取提示词模板列表失败: {str(e)}")
        raise


@router.get("/templates/{template_id}", response_model=PromptTemplateResponse)
async def get_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取提示词模板详情
    
    根据模板ID获取详细信息
    """
    try:
        Logger.info(f"用户 {current_user.id} 获取提示词模板: {template_id}")
        
        prompt_service = PromptService(db)
        template = await prompt_service.get_template(template_id, current_user.id)
        
        # 构建响应数据
        response = PromptTemplateResponse(
            id=template.id,
            name=template.name,
            description=template.description,
            category_id=template.category_id,
            content=template.content,
            variables=template.variables or [],
            tags=template.tags or [],
            is_system=template.is_system,
            is_active=template.is_active,
            owner_id=template.owner_id,
            usage_count=template.usage_count,
            last_used_at=template.last_used_at,
            created_at=template.created_at,
            updated_at=template.updated_at,
            category_name=template.category.name if template.category else None,
            owner_email=template.owner.email if template.owner else None
        )
        
        return response
        
    except Exception as e:
        Logger.error(f"获取提示词模板详情失败: {str(e)}")
        raise


@router.put("/templates/{template_id}", response_model=PromptTemplateResponse)
async def update_template(
    template_id: int,
    template_data: PromptTemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新提示词模板
    
    更新指定模板的信息，只有所有者可以更新
    """
    try:
        Logger.info(f"用户 {current_user.id} 更新提示词模板: {template_id}")
        
        prompt_service = PromptService(db)
        template = await prompt_service.update_template(template_id, template_data, current_user.id)
        
        # 构建响应数据
        response = PromptTemplateResponse(
            id=template.id,
            name=template.name,
            description=template.description,
            category_id=template.category_id,
            content=template.content,
            variables=template.variables or [],
            tags=template.tags or [],
            is_system=template.is_system,
            is_active=template.is_active,
            owner_id=template.owner_id,
            usage_count=template.usage_count,
            last_used_at=template.last_used_at,
            created_at=template.created_at,
            updated_at=template.updated_at,
            category_name=template.category.name if template.category else None,
            owner_email=template.owner.email if template.owner else None
        )
        
        return response
        
    except Exception as e:
        Logger.error(f"更新提示词模板失败: {str(e)}")
        raise


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除提示词模板
    
    软删除指定的模板，只有所有者可以删除
    """
    try:
        Logger.info(f"用户 {current_user.id} 删除提示词模板: {template_id}")
        
        prompt_service = PromptService(db)
        await prompt_service.delete_template(template_id, current_user.id)
        
    except Exception as e:
        Logger.error(f"删除提示词模板失败: {str(e)}")
        raise


@router.post("/templates/{template_id}/render", response_model=PromptTemplateRenderResponse)
async def render_template(
    template_id: int,
    render_request: PromptTemplateRenderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """渲染提示词模板
    
    使用提供的变量值渲染模板内容
    """
    try:
        Logger.info(f"用户 {current_user.id} 渲染提示词模板: {template_id}")
        
        prompt_service = PromptService(db)
        result = await prompt_service.render_template(
            template_id, 
            render_request.variables, 
            current_user.id
        )
        
        return result
        
    except Exception as e:
        Logger.error(f"渲染提示词模板失败: {str(e)}")
        raise


@router.post("/templates/validate", response_model=PromptTemplateValidateResponse)
async def validate_template(
    validate_request: PromptTemplateValidateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """验证提示词模板
    
    验证模板内容和变量定义的正确性
    """
    try:
        Logger.info(f"用户 {current_user.id} 验证提示词模板")
        
        prompt_service = PromptService(db)
        result = await prompt_service.validate_template(
            validate_request.content,
            validate_request.variables or []
        )
        
        return result
        
    except Exception as e:
        Logger.error(f"验证提示词模板失败: {str(e)}")
        raise


@router.get("/templates/{template_id}/usage-stats", response_model=List[PromptUsageStats])
async def get_template_usage_stats(
    template_id: int,
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取模板使用统计
    
    获取指定模板的使用统计数据和趋势
    """
    try:
        Logger.info(f"用户 {current_user.id} 获取模板使用统计: {template_id}")
        
        analytics_service = PromptAnalyticsService(db)
        stats = await analytics_service.get_usage_stats(
            template_id=template_id,
            include_trend=True
        )
        
        return stats
        
    except Exception as e:
        Logger.error(f"获取模板使用统计失败: {str(e)}")
        raise


@router.get("/templates/{template_id}/usage-logs")
async def get_template_usage_logs(
    template_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页大小"),
    success_only: Optional[bool] = Query(None, description="只显示成功记录"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取模板使用日志
    
    获取指定模板的详细使用日志
    """
    try:
        Logger.info(f"用户 {current_user.id} 获取模板使用日志: {template_id}")
        
        analytics_service = PromptAnalyticsService(db)
        logs, total = await analytics_service.get_usage_logs(
            template_id=template_id,
            success_only=success_only,
            page=page,
            page_size=page_size
        )
        
        return {
            "logs": logs,
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
    except Exception as e:
        Logger.error(f"获取模板使用日志失败: {str(e)}")
        raise

# 分
类管理API

@router.post("/categories", response_model=PromptCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: PromptCategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建提示词分类
    
    创建新的提示词分类，支持层级结构
    """
    try:
        Logger.info(f"用户 {current_user.id} 创建提示词分类: {category_data.name}")
        
        category_service = PromptCategoryService(db)
        category = await category_service.create_category(category_data)
        
        # 构建响应数据
        response = PromptCategoryResponse(
            id=category.id,
            name=category.name,
            description=category.description,
            parent_id=category.parent_id,
            sort_order=category.sort_order,
            is_active=category.is_active,
            template_count=category.template_count,
            created_at=category.created_at,
            updated_at=category.updated_at,
            parent_name=category.parent.name if category.parent else None,
            full_path=category.get_full_path(),
            children=[]
        )
        
        return response
        
    except Exception as e:
        Logger.error(f"创建提示词分类失败: {str(e)}")
        raise


@router.get("/categories", response_model=List[PromptCategoryResponse])
async def list_categories(
    parent_id: Optional[int] = Query(None, description="父分类ID"),
    include_children: bool = Query(False, description="是否包含子分类"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取提示词分类列表
    
    支持层级查询和子分类包含
    """
    try:
        Logger.info(f"用户 {current_user.id} 获取提示词分类列表")
        
        category_service = PromptCategoryService(db)
        categories = await category_service.list_categories(
            parent_id=parent_id,
            include_children=include_children
        )
        
        # 构建响应数据
        category_responses = []
        for category in categories:
            response = PromptCategoryResponse(
                id=category.id,
                name=category.name,
                description=category.description,
                parent_id=category.parent_id,
                sort_order=category.sort_order,
                is_active=category.is_active,
                template_count=category.template_count,
                created_at=category.created_at,
                updated_at=category.updated_at,
                parent_name=category.parent.name if category.parent else None,
                full_path=category.get_full_path(),
                children=[]
            )
            category_responses.append(response)
        
        return category_responses
        
    except Exception as e:
        Logger.error(f"获取提示词分类列表失败: {str(e)}")
        raise


@router.get("/categories/{category_id}", response_model=PromptCategoryResponse)
async def get_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取提示词分类详情
    
    根据分类ID获取详细信息
    """
    try:
        Logger.info(f"用户 {current_user.id} 获取提示词分类: {category_id}")
        
        category_service = PromptCategoryService(db)
        category = await category_service.get_category(category_id)
        
        # 构建响应数据
        response = PromptCategoryResponse(
            id=category.id,
            name=category.name,
            description=category.description,
            parent_id=category.parent_id,
            sort_order=category.sort_order,
            is_active=category.is_active,
            template_count=category.template_count,
            created_at=category.created_at,
            updated_at=category.updated_at,
            parent_name=category.parent.name if category.parent else None,
            full_path=category.get_full_path(),
            children=[]
        )
        
        return response
        
    except Exception as e:
        Logger.error(f"获取提示词分类详情失败: {str(e)}")
        raise


@router.put("/categories/{category_id}", response_model=PromptCategoryResponse)
async def update_category(
    category_id: int,
    category_data: PromptCategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新提示词分类
    
    更新指定分类的信息
    """
    try:
        Logger.info(f"用户 {current_user.id} 更新提示词分类: {category_id}")
        
        category_service = PromptCategoryService(db)
        category = await category_service.update_category(category_id, category_data)
        
        # 构建响应数据
        response = PromptCategoryResponse(
            id=category.id,
            name=category.name,
            description=category.description,
            parent_id=category.parent_id,
            sort_order=category.sort_order,
            is_active=category.is_active,
            template_count=category.template_count,
            created_at=category.created_at,
            updated_at=category.updated_at,
            parent_name=category.parent.name if category.parent else None,
            full_path=category.get_full_path(),
            children=[]
        )
        
        return response
        
    except Exception as e:
        Logger.error(f"更新提示词分类失败: {str(e)}")
        raise


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除提示词分类
    
    软删除指定的分类
    """
    try:
        Logger.info(f"用户 {current_user.id} 删除提示词分类: {category_id}")
        
        category_service = PromptCategoryService(db)
        await category_service.delete_category(category_id)
        
    except Exception as e:
        Logger.error(f"删除提示词分类失败: {str(e)}")
        raise


# 统计分析API

@router.get("/analytics/usage", response_model=List[PromptUsageStats])
async def get_usage_analytics(
    template_id: Optional[int] = Query(None, description="模板ID筛选"),
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    kb_id: Optional[int] = Query(None, description="知识库ID筛选"),
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取使用统计分析
    
    获取提示词使用的统计分析数据
    """
    try:
        Logger.info(f"用户 {current_user.id} 获取使用统计分析")
        
        analytics_service = PromptAnalyticsService(db)
        stats = await analytics_service.get_usage_stats(
            template_id=template_id,
            user_id=user_id,
            kb_id=kb_id,
            include_trend=True
        )
        
        return stats
        
    except Exception as e:
        Logger.error(f"获取使用统计分析失败: {str(e)}")
        raise


@router.get("/analytics/performance")
async def get_performance_analytics(
    template_id: Optional[int] = Query(None, description="模板ID筛选"),
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    kb_id: Optional[int] = Query(None, description="知识库ID筛选"),
    days: int = Query(30, ge=1, le=365, description="分析天数"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取性能分析
    
    获取提示词性能分析数据和优化建议
    """
    try:
        Logger.info(f"用户 {current_user.id} 获取性能分析")
        
        analytics_service = PromptAnalyticsService(db)
        performance = await analytics_service.analyze_performance(
            template_id=template_id,
            user_id=user_id,
            kb_id=kb_id,
            days=days
        )
        
        return performance
        
    except Exception as e:
        Logger.error(f"获取性能分析失败: {str(e)}")
        raise


@router.get("/analytics/top-templates")
async def get_top_templates(
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    kb_id: Optional[int] = Query(None, description="知识库ID筛选"),
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取热门模板排行
    
    获取使用量最高的模板排行榜
    """
    try:
        Logger.info(f"用户 {current_user.id} 获取热门模板排行")
        
        analytics_service = PromptAnalyticsService(db)
        top_templates = await analytics_service.get_top_templates_by_usage(
            user_id=user_id,
            kb_id=kb_id,
            days=days,
            limit=limit
        )
        
        return top_templates
        
    except Exception as e:
        Logger.error(f"获取热门模板排行失败: {str(e)}")
        raise


@router.get("/analytics/optimization-suggestions")
async def get_optimization_suggestions(
    template_id: Optional[int] = Query(None, description="模板ID筛选"),
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    kb_id: Optional[int] = Query(None, description="知识库ID筛选"),
    days: int = Query(30, ge=1, le=365, description="分析天数"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取优化建议
    
    基于使用数据提供优化建议
    """
    try:
        Logger.info(f"用户 {current_user.id} 获取优化建议")
        
        analytics_service = PromptAnalyticsService(db)
        suggestions = await analytics_service.get_optimization_suggestions(
            template_id=template_id,
            user_id=user_id,
            kb_id=kb_id,
            days=days
        )
        
        return suggestions
        
    except Exception as e:
        Logger.error(f"获取优化建议失败: {str(e)}")
        raise


@router.get("/analytics/anomalies")
async def detect_anomalies(
    template_id: Optional[int] = Query(None, description="模板ID筛选"),
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    kb_id: Optional[int] = Query(None, description="知识库ID筛选"),
    days: int = Query(7, ge=1, le=30, description="检测天数"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """检测异常使用情况
    
    检测提示词使用中的异常情况
    """
    try:
        Logger.info(f"用户 {current_user.id} 检测异常使用情况")
        
        analytics_service = PromptAnalyticsService(db)
        anomalies = await analytics_service.detect_anomalous_usage(
            template_id=template_id,
            user_id=user_id,
            kb_id=kb_id,
            days=days
        )
        
        return anomalies
        
    except Exception as e:
        Logger.error(f"检测异常使用情况失败: {str(e)}")
        raise
# 版本管理API


from app.services.prompt_version import PromptVersionService
from app.schemas.prompt import (
    PromptVersionCreate, PromptVersionResponse, PromptVersionList,
    PromptVersionCompareRequest, PromptVersionCompareResponse,
    PromptVersionRollbackRequest
)

@router.post("/templates/{template_id}/versions", response_model=PromptVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_version(
    template_id: int,
    version_data: PromptVersionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建新版本
    
    为指定模板创建新版本
    """
    try:
        Logger.info(f"用户 {current_user.id} 为模板 {template_id} 创建新版本")
        
        version_service = PromptVersionService(db)
        version = await version_service.create_version(template_id, version_data, current_user.id)
        
        # 构建响应数据
        response = PromptVersionResponse(
            id=version.id,
            template_id=version.template_id,
            version_number=version.version_number,
            content=version.content,
            variables=version.variables or [],
            change_log=version.change_log,
            is_published=version.is_published,
            is_current=version.is_current,
            created_by=version.created_by,
            created_at=version.created_at,
            published_at=version.published_at,
            creator_email=version.creator.email if version.creator else None
        )
        
        return response
        
    except Exception as e:
        Logger.error(f"创建版本失败: {str(e)}")
        raise


@router.get("/templates/{template_id}/versions", response_model=PromptVersionList)
async def get_version_history(
    template_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取版本历史
    
    获取指定模板的版本历史列表
    """
    try:
        Logger.info(f"用户 {current_user.id} 获取模板 {template_id} 的版本历史")
        
        version_service = PromptVersionService(db)
        versions, total = await version_service.get_version_history(
            template_id, current_user.id, page, page_size
        )
        
        # 获取模板名称
        prompt_service = PromptService(db)
        template = await prompt_service.get_template(template_id, current_user.id)
        
        # 构建响应数据
        version_responses = []
        for version in versions:
            response = PromptVersionResponse(
                id=version.id,
                template_id=version.template_id,
                version_number=version.version_number,
                content=version.content,
                variables=version.variables or [],
                change_log=version.change_log,
                is_published=version.is_published,
                is_current=version.is_current,
                created_by=version.created_by,
                created_at=version.created_at,
                published_at=version.published_at,
                creator_email=version.creator.email if version.creator else None
            )
            version_responses.append(response)
        
        return PromptVersionList(
            versions=version_responses,
            total=total,
            template_id=template_id,
            template_name=template.name
        )
        
    except Exception as e:
        Logger.error(f"获取版本历史失败: {str(e)}")
        raise


@router.post("/versions/{version_id}/publish", response_model=PromptVersionResponse)
async def publish_version(
    version_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """发布版本
    
    发布指定版本，使其生效
    """
    try:
        Logger.info(f"用户 {current_user.id} 发布版本: {version_id}")
        
        version_service = PromptVersionService(db)
        version = await version_service.publish_version(version_id, current_user.id)
        
        # 构建响应数据
        response = PromptVersionResponse(
            id=version.id,
            template_id=version.template_id,
            version_number=version.version_number,
            content=version.content,
            variables=version.variables or [],
            change_log=version.change_log,
            is_published=version.is_published,
            is_current=version.is_current,
            created_by=version.created_by,
            created_at=version.created_at,
            published_at=version.published_at,
            creator_email=version.creator.email if version.creator else None
        )
        
        return response
        
    except Exception as e:
        Logger.error(f"发布版本失败: {str(e)}")
        raise


@router.post("/templates/{template_id}/rollback", response_model=PromptTemplateResponse)
async def rollback_version(
    template_id: int,
    rollback_request: PromptVersionRollbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """版本回滚
    
    回滚模板到指定版本
    """
    try:
        Logger.info(f"用户 {current_user.id} 回滚模板 {template_id} 到版本 {rollback_request.version_id}")
        
        version_service = PromptVersionService(db)
        template = await version_service.rollback_version(template_id, rollback_request, current_user.id)
        
        # 构建响应数据
        response = PromptTemplateResponse(
            id=template.id,
            name=template.name,
            description=template.description,
            category_id=template.category_id,
            content=template.content,
            variables=template.variables or [],
            tags=template.tags or [],
            is_system=template.is_system,
            is_active=template.is_active,
            owner_id=template.owner_id,
            usage_count=template.usage_count,
            last_used_at=template.last_used_at,
            created_at=template.created_at,
            updated_at=template.updated_at,
            category_name=template.category.name if template.category else None,
            owner_email=template.owner.email if template.owner else None
        )
        
        return response
        
    except Exception as e:
        Logger.error(f"版本回滚失败: {str(e)}")
        raise


@router.post("/versions/compare", response_model=PromptVersionCompareResponse)
async def compare_versions(
    compare_request: PromptVersionCompareRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """比较版本
    
    比较两个版本之间的差异
    """
    try:
        Logger.info(f"用户 {current_user.id} 比较版本: {compare_request.version1_id} vs {compare_request.version2_id}")
        
        version_service = PromptVersionService(db)
        comparison = await version_service.compare_versions(compare_request)
        
        return comparison
        
    except Exception as e:
        Logger.error(f"版本比较失败: {str(e)}")
        raise