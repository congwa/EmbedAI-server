from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator, HttpUrl
from enum import Enum
from .base import CustomBaseModel

class WebhookStatus(str, Enum):
    """Webhook状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"
    SUSPENDED = "suspended"

class WebhookEvent(str, Enum):
    """Webhook事件类型枚举"""
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    KB_CREATED = "knowledge_base.created"
    KB_UPDATED = "knowledge_base.updated"
    KB_DELETED = "knowledge_base.deleted"
    DOC_UPLOADED = "document.uploaded"
    DOC_PROCESSED = "document.processed"
    DOC_FAILED = "document.failed"
    CHAT_STARTED = "chat.started"
    CHAT_ENDED = "chat.ended"
    SYSTEM_ALERT = "system.alert"

class IntegrationType(str, Enum):
    """集成类型枚举"""
    WEBHOOK = "webhook"
    API_CLIENT = "api_client"
    SSO = "sso"
    OAUTH = "oauth"
    CUSTOM = "custom"

class APIKeyScope(str, Enum):
    """API密钥权限范围枚举"""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    WEBHOOK = "webhook"

class APIKeyCreate(CustomBaseModel):
    """API密钥创建请求模型"""
    name: str = Field(..., description="密钥名称")
    description: Optional[str] = Field(None, description="密钥描述")
    scopes: List[APIKeyScope] = Field(..., description="权限范围")
    rate_limit: int = Field(1000, description="速率限制")
    expires_at: Optional[datetime] = Field(None, description="过期时间")

class APIKeyResponse(CustomBaseModel):
    """API密钥响应模型"""
    id: int = Field(..., description="密钥ID")
    name: str = Field(..., description="密钥名称")
    description: Optional[str] = Field(None, description="密钥描述")
    key_prefix: str = Field(..., description="密钥前缀")
    scopes: List[str] = Field(..., description="权限范围")
    rate_limit: int = Field(..., description="速率限制")
    is_active: bool = Field(..., description="是否激活")
    last_used_at: Optional[datetime] = Field(None, description="最后使用时间")
    usage_count: int = Field(..., description="使用次数")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    created_at: datetime = Field(..., description="创建时间")
    created_by: Optional[int] = Field(None, description="创建人")

class APIKeyCreateResponse(CustomBaseModel):
    """API密钥创建响应模型"""
    id: int = Field(..., description="密钥ID")
    name: str = Field(..., description="密钥名称")
    api_key: str = Field(..., description="完整API密钥")
    key_prefix: str = Field(..., description="密钥前缀")
    scopes: List[str] = Field(..., description="权限范围")
    expires_at: Optional[datetime] = Field(None, description="过期时间")

class WebhookCreate(CustomBaseModel):
    """Webhook创建请求模型"""
    name: str = Field(..., description="Webhook名称")
    description: Optional[str] = Field(None, description="Webhook描述")
    url: HttpUrl = Field(..., description="回调URL")
    secret: Optional[str] = Field(None, description="签名密钥")
    events: List[WebhookEvent] = Field(..., description="监听事件")
    headers: Optional[Dict[str, str]] = Field(None, description="自定义请求头")
    timeout: int = Field(30, description="超时时间(秒)")
    retry_count: int = Field(3, description="重试次数")

class WebhookUpdate(CustomBaseModel):
    """Webhook更新请求模型"""
    name: Optional[str] = Field(None, description="Webhook名称")
    description: Optional[str] = Field(None, description="Webhook描述")
    url: Optional[HttpUrl] = Field(None, description="回调URL")
    secret: Optional[str] = Field(None, description="签名密钥")
    events: Optional[List[WebhookEvent]] = Field(None, description="监听事件")
    headers: Optional[Dict[str, str]] = Field(None, description="自定义请求头")
    timeout: Optional[int] = Field(None, description="超时时间(秒)")
    retry_count: Optional[int] = Field(None, description="重试次数")
    is_active: Optional[bool] = Field(None, description="是否激活")

class WebhookResponse(CustomBaseModel):
    """Webhook响应模型"""
    id: int = Field(..., description="Webhook ID")
    name: str = Field(..., description="Webhook名称")
    description: Optional[str] = Field(None, description="Webhook描述")
    url: str = Field(..., description="回调URL")
    events: List[str] = Field(..., description="监听事件")
    headers: Optional[Dict[str, str]] = Field(None, description="自定义请求头")
    timeout: int = Field(..., description="超时时间(秒)")
    retry_count: int = Field(..., description="重试次数")
    status: WebhookStatus = Field(..., description="状态")
    is_active: bool = Field(..., description="是否激活")
    success_count: int = Field(..., description="成功次数")
    failure_count: int = Field(..., description="失败次数")
    last_triggered_at: Optional[datetime] = Field(None, description="最后触发时间")
    last_success_at: Optional[datetime] = Field(None, description="最后成功时间")
    last_failure_at: Optional[datetime] = Field(None, description="最后失败时间")
    created_at: datetime = Field(..., description="创建时间")
    created_by: Optional[int] = Field(None, description="创建人")

class WebhookDeliveryResponse(CustomBaseModel):
    """Webhook投递记录响应模型"""
    id: int = Field(..., description="投递ID")
    webhook_id: int = Field(..., description="Webhook ID")
    event_type: str = Field(..., description="事件类型")
    payload: Dict[str, Any] = Field(..., description="投递载荷")
    request_headers: Optional[Dict[str, str]] = Field(None, description="请求头")
    response_status: Optional[int] = Field(None, description="响应状态码")
    response_headers: Optional[Dict[str, str]] = Field(None, description="响应头")
    response_body: Optional[str] = Field(None, description="响应内容")
    duration_ms: Optional[int] = Field(None, description="请求耗时(毫秒)")
    is_success: bool = Field(..., description="是否成功")
    error_message: Optional[str] = Field(None, description="错误信息")
    retry_count: int = Field(..., description="重试次数")
    delivered_at: datetime = Field(..., description="投递时间")

class WebhookTestRequest(CustomBaseModel):
    """Webhook测试请求模型"""
    event_type: WebhookEvent = Field(..., description="测试事件类型")
    test_payload: Optional[Dict[str, Any]] = Field(None, description="测试载荷")

class IntegrationCreate(CustomBaseModel):
    """集成创建请求模型"""
    name: str = Field(..., description="集成名称")
    description: Optional[str] = Field(None, description="集成描述")
    integration_type: IntegrationType = Field(..., description="集成类型")
    provider: str = Field(..., description="提供商")
    config: Dict[str, Any] = Field(..., description="集成配置")
    credentials: Optional[Dict[str, Any]] = Field(None, description="认证凭据")

class IntegrationUpdate(CustomBaseModel):
    """集成更新请求模型"""
    name: Optional[str] = Field(None, description="集成名称")
    description: Optional[str] = Field(None, description="集成描述")
    config: Optional[Dict[str, Any]] = Field(None, description="集成配置")
    credentials: Optional[Dict[str, Any]] = Field(None, description="认证凭据")
    is_active: Optional[bool] = Field(None, description="是否激活")

class IntegrationResponse(CustomBaseModel):
    """集成响应模型"""
    id: int = Field(..., description="集成ID")
    name: str = Field(..., description="集成名称")
    description: Optional[str] = Field(None, description="集成描述")
    integration_type: str = Field(..., description="集成类型")
    provider: str = Field(..., description="提供商")
    config: Dict[str, Any] = Field(..., description="集成配置")
    is_active: bool = Field(..., description="是否激活")
    is_verified: bool = Field(..., description="是否已验证")
    last_sync_at: Optional[datetime] = Field(None, description="最后同步时间")
    sync_status: Optional[str] = Field(None, description="同步状态")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(..., description="创建时间")
    created_by: Optional[int] = Field(None, description="创建人")

class APIEndpointResponse(CustomBaseModel):
    """API端点响应模型"""
    id: int = Field(..., description="端点ID")
    path: str = Field(..., description="端点路径")
    method: str = Field(..., description="HTTP方法")
    summary: Optional[str] = Field(None, description="端点摘要")
    description: Optional[str] = Field(None, description="端点描述")
    tags: Optional[List[str]] = Field(None, description="端点标签")
    parameters: Optional[Dict[str, Any]] = Field(None, description="参数定义")
    request_schema: Optional[Dict[str, Any]] = Field(None, description="请求模式")
    response_schema: Optional[Dict[str, Any]] = Field(None, description="响应模式")
    examples: Optional[Dict[str, Any]] = Field(None, description="示例")
    is_deprecated: bool = Field(..., description="是否已弃用")
    is_public: bool = Field(..., description="是否公开")
    rate_limit: Optional[int] = Field(None, description="速率限制")
    auth_required: bool = Field(..., description="是否需要认证")
    scopes_required: Optional[List[str]] = Field(None, description="所需权限范围")
    version: str = Field(..., description="API版本")

class APIUsageStatsResponse(CustomBaseModel):
    """API使用统计响应模型"""
    total_requests: int = Field(..., description="总请求数")
    successful_requests: int = Field(..., description="成功请求数")
    failed_requests: int = Field(..., description="失败请求数")
    average_response_time: float = Field(..., description="平均响应时间")
    requests_by_endpoint: Dict[str, int] = Field(..., description="按端点统计请求")
    requests_by_status: Dict[str, int] = Field(..., description="按状态码统计请求")
    requests_by_hour: List[Dict[str, Any]] = Field(..., description="按小时统计请求")
    top_api_keys: List[Dict[str, Any]] = Field(..., description="热门API密钥")

class IntegrationTemplateResponse(CustomBaseModel):
    """集成模板响应模型"""
    id: int = Field(..., description="模板ID")
    name: str = Field(..., description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    provider: str = Field(..., description="提供商")
    integration_type: str = Field(..., description="集成类型")
    template_config: Dict[str, Any] = Field(..., description="模板配置")
    required_fields: Optional[List[str]] = Field(None, description="必填字段")
    optional_fields: Optional[List[str]] = Field(None, description="可选字段")
    documentation_url: Optional[str] = Field(None, description="文档链接")
    icon_url: Optional[str] = Field(None, description="图标链接")
    is_active: bool = Field(..., description="是否激活")
    usage_count: int = Field(..., description="使用次数")
    rating: Optional[float] = Field(None, description="评分")

class APIDocumentationCreate(CustomBaseModel):
    """API文档创建请求模型"""
    title: str = Field(..., description="文档标题")
    content: str = Field(..., description="文档内容")
    content_type: str = Field("markdown", description="内容类型")
    category: Optional[str] = Field(None, description="文档分类")
    tags: Optional[List[str]] = Field(None, description="文档标签")
    version: str = Field("v1", description="API版本")
    order_index: int = Field(0, description="排序索引")
    is_published: bool = Field(False, description="是否已发布")
    is_featured: bool = Field(False, description="是否推荐")

class APIDocumentationUpdate(CustomBaseModel):
    """API文档更新请求模型"""
    title: Optional[str] = Field(None, description="文档标题")
    content: Optional[str] = Field(None, description="文档内容")
    content_type: Optional[str] = Field(None, description="内容类型")
    category: Optional[str] = Field(None, description="文档分类")
    tags: Optional[List[str]] = Field(None, description="文档标签")
    order_index: Optional[int] = Field(None, description="排序索引")
    is_published: Optional[bool] = Field(None, description="是否已发布")
    is_featured: Optional[bool] = Field(None, description="是否推荐")

class APIDocumentationResponse(CustomBaseModel):
    """API文档响应模型"""
    id: int = Field(..., description="文档ID")
    title: str = Field(..., description="文档标题")
    content: str = Field(..., description="文档内容")
    content_type: str = Field(..., description="内容类型")
    category: Optional[str] = Field(None, description="文档分类")
    tags: Optional[List[str]] = Field(None, description="文档标签")
    version: str = Field(..., description="API版本")
    order_index: int = Field(..., description="排序索引")
    is_published: bool = Field(..., description="是否已发布")
    is_featured: bool = Field(..., description="是否推荐")
    view_count: int = Field(..., description="浏览次数")
    last_viewed_at: Optional[datetime] = Field(None, description="最后浏览时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    created_by: Optional[int] = Field(None, description="创建人")

class IntegrationDashboardResponse(CustomBaseModel):
    """集成管理仪表板响应模型"""
    total_integrations: int = Field(..., description="总集成数")
    active_integrations: int = Field(..., description="活跃集成数")
    total_webhooks: int = Field(..., description="总Webhook数")
    active_webhooks: int = Field(..., description="活跃Webhook数")
    total_api_keys: int = Field(..., description="总API密钥数")
    active_api_keys: int = Field(..., description="活跃API密钥数")
    api_requests_24h: int = Field(..., description="24小时API请求数")
    webhook_deliveries_24h: int = Field(..., description="24小时Webhook投递数")
    recent_api_usage: List[Dict[str, Any]] = Field(..., description="最近API使用")
    recent_webhook_deliveries: List[WebhookDeliveryResponse] = Field(..., description="最近Webhook投递")
    integration_by_type: Dict[str, int] = Field(..., description="按类型统计集成")
    webhook_success_rate: float = Field(..., description="Webhook成功率")

class WebhookEventPayload(CustomBaseModel):
    """Webhook事件载荷模型"""
    event_type: str = Field(..., description="事件类型")
    timestamp: datetime = Field(..., description="事件时间戳")
    data: Dict[str, Any] = Field(..., description="事件数据")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")

class APIKeyUsageRequest(CustomBaseModel):
    """API密钥使用统计请求模型"""
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    group_by: str = Field("day", description="分组方式")

    @validator('group_by')
    def validate_group_by(cls, v):
        allowed_values = ['hour', 'day', 'week', 'month']
        if v not in allowed_values:
            raise ValueError(f'分组方式必须是以下之一: {", ".join(allowed_values)}')
        return v
