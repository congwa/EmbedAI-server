from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime
import enum

class WebhookStatus(enum.Enum):
    """Webhook状态枚举"""
    ACTIVE = "active"         # 激活
    INACTIVE = "inactive"     # 未激活
    FAILED = "failed"         # 失败
    SUSPENDED = "suspended"   # 暂停

class WebhookEvent(enum.Enum):
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

class IntegrationType(enum.Enum):
    """集成类型枚举"""
    WEBHOOK = "webhook"           # Webhook集成
    API_CLIENT = "api_client"     # API客户端
    SSO = "sso"                  # 单点登录
    OAUTH = "oauth"              # OAuth认证
    CUSTOM = "custom"            # 自定义集成

class APIKeyScope(enum.Enum):
    """API密钥权限范围枚举"""
    READ = "read"                # 只读权限
    WRITE = "write"              # 写入权限
    ADMIN = "admin"              # 管理员权限
    WEBHOOK = "webhook"          # Webhook权限

class APIKey(Base):
    """API密钥模型
    
    管理第三方集成的API密钥
    """
    __tablename__ = "api_keys"
    __table_args__ = {'comment': 'API密钥表，管理第三方集成密钥'}

    id = Column(Integer, primary_key=True, index=True, comment='密钥ID')
    name = Column(String(100), nullable=False, comment='密钥名称')
    description = Column(Text, nullable=True, comment='密钥描述')
    key_hash = Column(String(255), nullable=False, unique=True, comment='密钥哈希')
    key_prefix = Column(String(20), nullable=False, comment='密钥前缀')
    scopes = Column(JSON, nullable=False, comment='权限范围')
    rate_limit = Column(Integer, default=1000, comment='速率限制')
    is_active = Column(Boolean, default=True, comment='是否激活')
    last_used_at = Column(DateTime, nullable=True, comment='最后使用时间')
    usage_count = Column(Integer, default=0, comment='使用次数')
    expires_at = Column(DateTime, nullable=True, comment='过期时间')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    created_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, comment='创建人')
    
    # 关系定义
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<APIKey(name={self.name}, prefix={self.key_prefix})>"

class Webhook(Base):
    """Webhook模型
    
    管理Webhook配置和状态
    """
    __tablename__ = "webhooks"
    __table_args__ = {'comment': 'Webhook表，管理Webhook配置'}

    id = Column(Integer, primary_key=True, index=True, comment='Webhook ID')
    name = Column(String(100), nullable=False, comment='Webhook名称')
    description = Column(Text, nullable=True, comment='Webhook描述')
    url = Column(String(500), nullable=False, comment='回调URL')
    secret = Column(String(255), nullable=True, comment='签名密钥')
    events = Column(JSON, nullable=False, comment='监听事件')
    headers = Column(JSON, nullable=True, comment='自定义请求头')
    timeout = Column(Integer, default=30, comment='超时时间(秒)')
    retry_count = Column(Integer, default=3, comment='重试次数')
    status = Column(String(20), nullable=False, default=WebhookStatus.ACTIVE.value, comment='状态')
    is_active = Column(Boolean, default=True, comment='是否激活')
    success_count = Column(Integer, default=0, comment='成功次数')
    failure_count = Column(Integer, default=0, comment='失败次数')
    last_triggered_at = Column(DateTime, nullable=True, comment='最后触发时间')
    last_success_at = Column(DateTime, nullable=True, comment='最后成功时间')
    last_failure_at = Column(DateTime, nullable=True, comment='最后失败时间')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    created_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, comment='创建人')
    
    # 关系定义
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<Webhook(name={self.name}, url={self.url})>"

class WebhookDelivery(Base):
    """Webhook投递记录模型
    
    记录Webhook投递历史和状态
    """
    __tablename__ = "webhook_deliveries"
    __table_args__ = {'comment': 'Webhook投递记录表'}

    id = Column(Integer, primary_key=True, index=True, comment='投递ID')
    webhook_id = Column(Integer, ForeignKey('webhooks.id', ondelete='CASCADE'), nullable=False, comment='Webhook ID')
    event_type = Column(String(50), nullable=False, comment='事件类型')
    payload = Column(JSON, nullable=False, comment='投递载荷')
    request_headers = Column(JSON, nullable=True, comment='请求头')
    response_status = Column(Integer, nullable=True, comment='响应状态码')
    response_headers = Column(JSON, nullable=True, comment='响应头')
    response_body = Column(Text, nullable=True, comment='响应内容')
    duration_ms = Column(Integer, nullable=True, comment='请求耗时(毫秒)')
    is_success = Column(Boolean, default=False, comment='是否成功')
    error_message = Column(Text, nullable=True, comment='错误信息')
    retry_count = Column(Integer, default=0, comment='重试次数')
    delivered_at = Column(DateTime, default=datetime.now, comment='投递时间')
    
    # 关系定义
    webhook = relationship("Webhook", backref="deliveries")
    
    def __repr__(self):
        return f"<WebhookDelivery(webhook_id={self.webhook_id}, event={self.event_type})>"

class Integration(Base):
    """集成配置模型
    
    管理第三方系统集成配置
    """
    __tablename__ = "integrations"
    __table_args__ = {'comment': '集成配置表，管理第三方系统集成'}

    id = Column(Integer, primary_key=True, index=True, comment='集成ID')
    name = Column(String(100), nullable=False, comment='集成名称')
    description = Column(Text, nullable=True, comment='集成描述')
    integration_type = Column(String(50), nullable=False, comment='集成类型')
    provider = Column(String(100), nullable=False, comment='提供商')
    config = Column(JSON, nullable=False, comment='集成配置')
    credentials = Column(JSON, nullable=True, comment='认证凭据')
    is_active = Column(Boolean, default=True, comment='是否激活')
    is_verified = Column(Boolean, default=False, comment='是否已验证')
    last_sync_at = Column(DateTime, nullable=True, comment='最后同步时间')
    sync_status = Column(String(20), nullable=True, comment='同步状态')
    error_message = Column(Text, nullable=True, comment='错误信息')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    created_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, comment='创建人')
    
    # 关系定义
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<Integration(name={self.name}, type={self.integration_type})>"

class APIEndpoint(Base):
    """API端点模型
    
    记录和管理API端点信息
    """
    __tablename__ = "api_endpoints"
    __table_args__ = {'comment': 'API端点表，记录API端点信息'}

    id = Column(Integer, primary_key=True, index=True, comment='端点ID')
    path = Column(String(255), nullable=False, comment='端点路径')
    method = Column(String(10), nullable=False, comment='HTTP方法')
    summary = Column(String(255), nullable=True, comment='端点摘要')
    description = Column(Text, nullable=True, comment='端点描述')
    tags = Column(JSON, nullable=True, comment='端点标签')
    parameters = Column(JSON, nullable=True, comment='参数定义')
    request_schema = Column(JSON, nullable=True, comment='请求模式')
    response_schema = Column(JSON, nullable=True, comment='响应模式')
    examples = Column(JSON, nullable=True, comment='示例')
    is_deprecated = Column(Boolean, default=False, comment='是否已弃用')
    is_public = Column(Boolean, default=True, comment='是否公开')
    rate_limit = Column(Integer, nullable=True, comment='速率限制')
    auth_required = Column(Boolean, default=True, comment='是否需要认证')
    scopes_required = Column(JSON, nullable=True, comment='所需权限范围')
    version = Column(String(20), nullable=False, default='v1', comment='API版本')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def __repr__(self):
        return f"<APIEndpoint(method={self.method}, path={self.path})>"

class APIUsageLog(Base):
    """API使用日志模型
    
    记录API调用统计和使用情况
    """
    __tablename__ = "api_usage_logs"
    __table_args__ = {'comment': 'API使用日志表，记录API调用统计'}

    id = Column(Integer, primary_key=True, index=True, comment='日志ID')
    api_key_id = Column(Integer, ForeignKey('api_keys.id', ondelete='SET NULL'), nullable=True, comment='API密钥ID')
    endpoint_id = Column(Integer, ForeignKey('api_endpoints.id', ondelete='SET NULL'), nullable=True, comment='端点ID')
    method = Column(String(10), nullable=False, comment='HTTP方法')
    path = Column(String(255), nullable=False, comment='请求路径')
    status_code = Column(Integer, nullable=False, comment='响应状态码')
    response_time_ms = Column(Integer, nullable=True, comment='响应时间(毫秒)')
    request_size = Column(Integer, nullable=True, comment='请求大小(字节)')
    response_size = Column(Integer, nullable=True, comment='响应大小(字节)')
    ip_address = Column(String(45), nullable=True, comment='客户端IP')
    user_agent = Column(Text, nullable=True, comment='用户代理')
    error_message = Column(Text, nullable=True, comment='错误信息')
    created_at = Column(DateTime, default=datetime.now, index=True, comment='创建时间')
    
    # 关系定义
    api_key = relationship("APIKey", backref="usage_logs")
    endpoint = relationship("APIEndpoint", backref="usage_logs")
    
    def __repr__(self):
        return f"<APIUsageLog(method={self.method}, path={self.path}, status={self.status_code})>"

class IntegrationTemplate(Base):
    """集成模板模型
    
    预定义的集成配置模板
    """
    __tablename__ = "integration_templates"
    __table_args__ = {'comment': '集成模板表，预定义集成配置'}

    id = Column(Integer, primary_key=True, index=True, comment='模板ID')
    name = Column(String(100), nullable=False, comment='模板名称')
    description = Column(Text, nullable=True, comment='模板描述')
    provider = Column(String(100), nullable=False, comment='提供商')
    integration_type = Column(String(50), nullable=False, comment='集成类型')
    template_config = Column(JSON, nullable=False, comment='模板配置')
    required_fields = Column(JSON, nullable=True, comment='必填字段')
    optional_fields = Column(JSON, nullable=True, comment='可选字段')
    documentation_url = Column(String(500), nullable=True, comment='文档链接')
    icon_url = Column(String(500), nullable=True, comment='图标链接')
    is_active = Column(Boolean, default=True, comment='是否激活')
    usage_count = Column(Integer, default=0, comment='使用次数')
    rating = Column(Float, nullable=True, comment='评分')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def __repr__(self):
        return f"<IntegrationTemplate(name={self.name}, provider={self.provider})>"

class APIDocumentation(Base):
    """API文档模型
    
    管理API文档内容和版本
    """
    __tablename__ = "api_documentation"
    __table_args__ = {'comment': 'API文档表，管理API文档内容'}

    id = Column(Integer, primary_key=True, index=True, comment='文档ID')
    title = Column(String(255), nullable=False, comment='文档标题')
    content = Column(Text, nullable=False, comment='文档内容')
    content_type = Column(String(50), nullable=False, default='markdown', comment='内容类型')
    category = Column(String(100), nullable=True, comment='文档分类')
    tags = Column(JSON, nullable=True, comment='文档标签')
    version = Column(String(20), nullable=False, default='v1', comment='API版本')
    order_index = Column(Integer, default=0, comment='排序索引')
    is_published = Column(Boolean, default=False, comment='是否已发布')
    is_featured = Column(Boolean, default=False, comment='是否推荐')
    view_count = Column(Integer, default=0, comment='浏览次数')
    last_viewed_at = Column(DateTime, nullable=True, comment='最后浏览时间')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    created_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, comment='创建人')
    
    # 关系定义
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<APIDocumentation(title={self.title}, version={self.version})>"
