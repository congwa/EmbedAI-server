from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.services.auth import get_current_admin_user
from app.services.integration import IntegrationService
from app.core.response import APIResponse, ResponseModel
from app.schemas.integration import (
    APIKeyCreate, APIKeyResponse, APIKeyCreateResponse,
    WebhookCreate, WebhookUpdate, WebhookResponse,
    WebhookDeliveryResponse, WebhookTestRequest,
    IntegrationCreate, IntegrationUpdate, IntegrationResponse,
    APIEndpointResponse, APIUsageStatsResponse,
    IntegrationTemplateResponse, APIDocumentationCreate,
    APIDocumentationUpdate, APIDocumentationResponse,
    IntegrationDashboardResponse, APIKeyUsageRequest
)
from app.models.user import User
from app.core.logger import Logger

router = APIRouter(tags=["admin-integration"])

# ==================== 集成管理仪表板 ====================

@router.get("/dashboard", response_model=ResponseModel[IntegrationDashboardResponse])
async def get_integration_dashboard(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取集成管理仪表板数据"""
    try:
        integration_service = IntegrationService(db)
        dashboard_data = await integration_service.get_integration_dashboard()
        return APIResponse.success(data=dashboard_data)
        
    except Exception as e:
        Logger.error(f"获取集成管理仪表板数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取集成管理仪表板数据失败")

# ==================== API密钥管理 ====================

@router.post("/api-keys", response_model=ResponseModel[APIKeyCreateResponse])
async def create_api_key(
    key_data: APIKeyCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """创建API密钥"""
    try:
        integration_service = IntegrationService(db)
        api_key = await integration_service.create_api_key(key_data, current_admin.id)
        return APIResponse.success(data=api_key)
        
    except Exception as e:
        Logger.error(f"创建API密钥失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建API密钥失败")

@router.get("/api-keys", response_model=ResponseModel[List[APIKeyResponse]])
async def get_api_keys(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取API密钥列表"""
    try:
        integration_service = IntegrationService(db)
        api_keys = await integration_service.get_api_keys(skip, limit, is_active)
        return APIResponse.success(data=api_keys)
        
    except Exception as e:
        Logger.error(f"获取API密钥列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取API密钥列表失败")

@router.delete("/api-keys/{key_id}", response_model=ResponseModel[bool])
async def revoke_api_key(
    key_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """撤销API密钥"""
    try:
        integration_service = IntegrationService(db)
        result = await integration_service.revoke_api_key(key_id)
        return APIResponse.success(data=result)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        Logger.error(f"撤销API密钥失败: {str(e)}")
        raise HTTPException(status_code=500, detail="撤销API密钥失败")

@router.get("/api-keys/usage-stats", response_model=ResponseModel[APIUsageStatsResponse])
async def get_api_usage_stats(
    usage_request: APIKeyUsageRequest = Depends(),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取API使用统计"""
    try:
        integration_service = IntegrationService(db)
        stats = await integration_service.get_api_usage_stats(
            usage_request.start_date,
            usage_request.end_date
        )
        return APIResponse.success(data=stats)
        
    except Exception as e:
        Logger.error(f"获取API使用统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取API使用统计失败")

# ==================== Webhook管理 ====================

@router.post("/webhooks", response_model=ResponseModel[WebhookResponse])
async def create_webhook(
    webhook_data: WebhookCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """创建Webhook"""
    try:
        integration_service = IntegrationService(db)
        webhook = await integration_service.create_webhook(webhook_data, current_admin.id)
        return APIResponse.success(data=webhook)
        
    except Exception as e:
        Logger.error(f"创建Webhook失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建Webhook失败")

@router.get("/webhooks", response_model=ResponseModel[List[WebhookResponse]])
async def get_webhooks(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取Webhook列表"""
    try:
        # 这里需要在IntegrationService中实现get_webhooks方法
        # 为了简化，暂时返回空列表
        return APIResponse.success(data=[])
        
    except Exception as e:
        Logger.error(f"获取Webhook列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取Webhook列表失败")

@router.put("/webhooks/{webhook_id}", response_model=ResponseModel[WebhookResponse])
async def update_webhook(
    webhook_id: int,
    webhook_data: WebhookUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """更新Webhook"""
    try:
        integration_service = IntegrationService(db)
        webhook = await integration_service.update_webhook(webhook_id, webhook_data)
        return APIResponse.success(data=webhook)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        Logger.error(f"更新Webhook失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新Webhook失败")

@router.post("/webhooks/{webhook_id}/test", response_model=ResponseModel[WebhookDeliveryResponse])
async def test_webhook(
    webhook_id: int,
    test_request: WebhookTestRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """测试Webhook"""
    try:
        integration_service = IntegrationService(db)
        delivery = await integration_service.test_webhook(webhook_id, test_request)
        return APIResponse.success(data=delivery)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        Logger.error(f"测试Webhook失败: {str(e)}")
        raise HTTPException(status_code=500, detail="测试Webhook失败")

@router.get("/webhooks/{webhook_id}/deliveries", response_model=ResponseModel[List[WebhookDeliveryResponse]])
async def get_webhook_deliveries(
    webhook_id: int,
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取Webhook投递记录"""
    try:
        # 这里需要在IntegrationService中实现get_webhook_deliveries方法
        # 为了简化，暂时返回空列表
        return APIResponse.success(data=[])
        
    except Exception as e:
        Logger.error(f"获取Webhook投递记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取Webhook投递记录失败")

# ==================== 第三方集成管理 ====================

@router.post("/integrations", response_model=ResponseModel[IntegrationResponse])
async def create_integration(
    integration_data: IntegrationCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """创建第三方集成"""
    try:
        integration_service = IntegrationService(db)
        integration = await integration_service.create_integration(integration_data, current_admin.id)
        return APIResponse.success(data=integration)
        
    except Exception as e:
        Logger.error(f"创建第三方集成失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建第三方集成失败")

@router.get("/integrations", response_model=ResponseModel[List[IntegrationResponse]])
async def get_integrations(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    integration_type: Optional[str] = Query(None, description="集成类型"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取第三方集成列表"""
    try:
        # 这里需要在IntegrationService中实现get_integrations方法
        # 为了简化，暂时返回空列表
        return APIResponse.success(data=[])
        
    except Exception as e:
        Logger.error(f"获取第三方集成列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取第三方集成列表失败")

@router.get("/integration-templates", response_model=ResponseModel[List[IntegrationTemplateResponse]])
async def get_integration_templates(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    provider: Optional[str] = Query(None, description="提供商"),
    integration_type: Optional[str] = Query(None, description="集成类型"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取集成模板列表"""
    try:
        # 这里需要在IntegrationService中实现get_integration_templates方法
        # 为了简化，暂时返回空列表
        return APIResponse.success(data=[])
        
    except Exception as e:
        Logger.error(f"获取集成模板列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取集成模板列表失败")

# ==================== API文档管理 ====================

@router.post("/documentation", response_model=ResponseModel[APIDocumentationResponse])
async def create_api_documentation(
    doc_data: APIDocumentationCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """创建API文档"""
    try:
        integration_service = IntegrationService(db)
        documentation = await integration_service.create_api_documentation(doc_data, current_admin.id)
        return APIResponse.success(data=documentation)
        
    except Exception as e:
        Logger.error(f"创建API文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建API文档失败")

@router.get("/documentation", response_model=ResponseModel[List[APIDocumentationResponse]])
async def get_api_documentation(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    category: Optional[str] = Query(None, description="文档分类"),
    version: Optional[str] = Query(None, description="API版本"),
    is_published: Optional[bool] = Query(None, description="是否已发布"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取API文档列表"""
    try:
        integration_service = IntegrationService(db)
        documentation = await integration_service.get_api_documentation(
            skip, limit, category, version, is_published
        )
        return APIResponse.success(data=documentation)
        
    except Exception as e:
        Logger.error(f"获取API文档列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取API文档列表失败")

@router.put("/documentation/{doc_id}", response_model=ResponseModel[APIDocumentationResponse])
async def update_api_documentation(
    doc_id: int,
    doc_data: APIDocumentationUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """更新API文档"""
    try:
        # 这里需要在IntegrationService中实现update_api_documentation方法
        # 为了简化，暂时返回错误
        raise HTTPException(status_code=404, detail="API文档不存在")
        
    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"更新API文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新API文档失败")

@router.delete("/documentation/{doc_id}", response_model=ResponseModel[bool])
async def delete_api_documentation(
    doc_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """删除API文档"""
    try:
        # 这里需要在IntegrationService中实现delete_api_documentation方法
        # 为了简化，暂时返回True
        return APIResponse.success(data=True)
        
    except Exception as e:
        Logger.error(f"删除API文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail="删除API文档失败")

# ==================== API端点管理 ====================

@router.get("/endpoints", response_model=ResponseModel[List[APIEndpointResponse]])
async def get_api_endpoints(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    version: Optional[str] = Query(None, description="API版本"),
    is_public: Optional[bool] = Query(None, description="是否公开"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取API端点列表"""
    try:
        # 这里需要在IntegrationService中实现get_api_endpoints方法
        # 为了简化，暂时返回空列表
        return APIResponse.success(data=[])
        
    except Exception as e:
        Logger.error(f"获取API端点列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取API端点列表失败")
