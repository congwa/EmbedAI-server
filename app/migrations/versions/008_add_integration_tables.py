"""Add integration management tables

Revision ID: 008
Revises: 007
Create Date: 2024-08-04 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    # Create api_keys table
    op.create_table('api_keys',
        sa.Column('id', sa.Integer(), nullable=False, comment='密钥ID'),
        sa.Column('name', sa.String(length=100), nullable=False, comment='密钥名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='密钥描述'),
        sa.Column('key_hash', sa.String(length=255), nullable=False, comment='密钥哈希'),
        sa.Column('key_prefix', sa.String(length=20), nullable=False, comment='密钥前缀'),
        sa.Column('scopes', sa.JSON(), nullable=False, comment='权限范围'),
        sa.Column('rate_limit', sa.Integer(), nullable=True, comment='速率限制'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否激活'),
        sa.Column('last_used_at', sa.DateTime(), nullable=True, comment='最后使用时间'),
        sa.Column('usage_count', sa.Integer(), nullable=True, comment='使用次数'),
        sa.Column('expires_at', sa.DateTime(), nullable=True, comment='过期时间'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash'),
        comment='API密钥表，管理第三方集成密钥'
    )
    op.create_index(op.f('ix_api_keys_id'), 'api_keys', ['id'], unique=False)

    # Create webhooks table
    op.create_table('webhooks',
        sa.Column('id', sa.Integer(), nullable=False, comment='Webhook ID'),
        sa.Column('name', sa.String(length=100), nullable=False, comment='Webhook名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='Webhook描述'),
        sa.Column('url', sa.String(length=500), nullable=False, comment='回调URL'),
        sa.Column('secret', sa.String(length=255), nullable=True, comment='签名密钥'),
        sa.Column('events', sa.JSON(), nullable=False, comment='监听事件'),
        sa.Column('headers', sa.JSON(), nullable=True, comment='自定义请求头'),
        sa.Column('timeout', sa.Integer(), nullable=True, comment='超时时间(秒)'),
        sa.Column('retry_count', sa.Integer(), nullable=True, comment='重试次数'),
        sa.Column('status', sa.String(length=20), nullable=False, comment='状态'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否激活'),
        sa.Column('success_count', sa.Integer(), nullable=True, comment='成功次数'),
        sa.Column('failure_count', sa.Integer(), nullable=True, comment='失败次数'),
        sa.Column('last_triggered_at', sa.DateTime(), nullable=True, comment='最后触发时间'),
        sa.Column('last_success_at', sa.DateTime(), nullable=True, comment='最后成功时间'),
        sa.Column('last_failure_at', sa.DateTime(), nullable=True, comment='最后失败时间'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='Webhook表，管理Webhook配置'
    )
    op.create_index(op.f('ix_webhooks_id'), 'webhooks', ['id'], unique=False)

    # Create webhook_deliveries table
    op.create_table('webhook_deliveries',
        sa.Column('id', sa.Integer(), nullable=False, comment='投递ID'),
        sa.Column('webhook_id', sa.Integer(), nullable=False, comment='Webhook ID'),
        sa.Column('event_type', sa.String(length=50), nullable=False, comment='事件类型'),
        sa.Column('payload', sa.JSON(), nullable=False, comment='投递载荷'),
        sa.Column('request_headers', sa.JSON(), nullable=True, comment='请求头'),
        sa.Column('response_status', sa.Integer(), nullable=True, comment='响应状态码'),
        sa.Column('response_headers', sa.JSON(), nullable=True, comment='响应头'),
        sa.Column('response_body', sa.Text(), nullable=True, comment='响应内容'),
        sa.Column('duration_ms', sa.Integer(), nullable=True, comment='请求耗时(毫秒)'),
        sa.Column('is_success', sa.Boolean(), nullable=True, comment='是否成功'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息'),
        sa.Column('retry_count', sa.Integer(), nullable=True, comment='重试次数'),
        sa.Column('delivered_at', sa.DateTime(), nullable=True, comment='投递时间'),
        sa.ForeignKeyConstraint(['webhook_id'], ['webhooks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Webhook投递记录表'
    )
    op.create_index(op.f('ix_webhook_deliveries_id'), 'webhook_deliveries', ['id'], unique=False)

    # Create integrations table
    op.create_table('integrations',
        sa.Column('id', sa.Integer(), nullable=False, comment='集成ID'),
        sa.Column('name', sa.String(length=100), nullable=False, comment='集成名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='集成描述'),
        sa.Column('integration_type', sa.String(length=50), nullable=False, comment='集成类型'),
        sa.Column('provider', sa.String(length=100), nullable=False, comment='提供商'),
        sa.Column('config', sa.JSON(), nullable=False, comment='集成配置'),
        sa.Column('credentials', sa.JSON(), nullable=True, comment='认证凭据'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否激活'),
        sa.Column('is_verified', sa.Boolean(), nullable=True, comment='是否已验证'),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True, comment='最后同步时间'),
        sa.Column('sync_status', sa.String(length=20), nullable=True, comment='同步状态'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='集成配置表，管理第三方系统集成'
    )
    op.create_index(op.f('ix_integrations_id'), 'integrations', ['id'], unique=False)

    # Create api_endpoints table
    op.create_table('api_endpoints',
        sa.Column('id', sa.Integer(), nullable=False, comment='端点ID'),
        sa.Column('path', sa.String(length=255), nullable=False, comment='端点路径'),
        sa.Column('method', sa.String(length=10), nullable=False, comment='HTTP方法'),
        sa.Column('summary', sa.String(length=255), nullable=True, comment='端点摘要'),
        sa.Column('description', sa.Text(), nullable=True, comment='端点描述'),
        sa.Column('tags', sa.JSON(), nullable=True, comment='端点标签'),
        sa.Column('parameters', sa.JSON(), nullable=True, comment='参数定义'),
        sa.Column('request_schema', sa.JSON(), nullable=True, comment='请求模式'),
        sa.Column('response_schema', sa.JSON(), nullable=True, comment='响应模式'),
        sa.Column('examples', sa.JSON(), nullable=True, comment='示例'),
        sa.Column('is_deprecated', sa.Boolean(), nullable=True, comment='是否已弃用'),
        sa.Column('is_public', sa.Boolean(), nullable=True, comment='是否公开'),
        sa.Column('rate_limit', sa.Integer(), nullable=True, comment='速率限制'),
        sa.Column('auth_required', sa.Boolean(), nullable=True, comment='是否需要认证'),
        sa.Column('scopes_required', sa.JSON(), nullable=True, comment='所需权限范围'),
        sa.Column('version', sa.String(length=20), nullable=False, comment='API版本'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='API端点表，记录API端点信息'
    )
    op.create_index(op.f('ix_api_endpoints_id'), 'api_endpoints', ['id'], unique=False)

    # Create api_usage_logs table
    op.create_table('api_usage_logs',
        sa.Column('id', sa.Integer(), nullable=False, comment='日志ID'),
        sa.Column('api_key_id', sa.Integer(), nullable=True, comment='API密钥ID'),
        sa.Column('endpoint_id', sa.Integer(), nullable=True, comment='端点ID'),
        sa.Column('method', sa.String(length=10), nullable=False, comment='HTTP方法'),
        sa.Column('path', sa.String(length=255), nullable=False, comment='请求路径'),
        sa.Column('status_code', sa.Integer(), nullable=False, comment='响应状态码'),
        sa.Column('response_time_ms', sa.Integer(), nullable=True, comment='响应时间(毫秒)'),
        sa.Column('request_size', sa.Integer(), nullable=True, comment='请求大小(字节)'),
        sa.Column('response_size', sa.Integer(), nullable=True, comment='响应大小(字节)'),
        sa.Column('ip_address', sa.String(length=45), nullable=True, comment='客户端IP'),
        sa.Column('user_agent', sa.Text(), nullable=True, comment='用户代理'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.ForeignKeyConstraint(['api_key_id'], ['api_keys.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['endpoint_id'], ['api_endpoints.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='API使用日志表，记录API调用统计'
    )
    op.create_index(op.f('ix_api_usage_logs_id'), 'api_usage_logs', ['id'], unique=False)
    op.create_index(op.f('ix_api_usage_logs_created_at'), 'api_usage_logs', ['created_at'], unique=False)

    # Create integration_templates table
    op.create_table('integration_templates',
        sa.Column('id', sa.Integer(), nullable=False, comment='模板ID'),
        sa.Column('name', sa.String(length=100), nullable=False, comment='模板名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='模板描述'),
        sa.Column('provider', sa.String(length=100), nullable=False, comment='提供商'),
        sa.Column('integration_type', sa.String(length=50), nullable=False, comment='集成类型'),
        sa.Column('template_config', sa.JSON(), nullable=False, comment='模板配置'),
        sa.Column('required_fields', sa.JSON(), nullable=True, comment='必填字段'),
        sa.Column('optional_fields', sa.JSON(), nullable=True, comment='可选字段'),
        sa.Column('documentation_url', sa.String(length=500), nullable=True, comment='文档链接'),
        sa.Column('icon_url', sa.String(length=500), nullable=True, comment='图标链接'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否激活'),
        sa.Column('usage_count', sa.Integer(), nullable=True, comment='使用次数'),
        sa.Column('rating', sa.Float(), nullable=True, comment='评分'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='集成模板表，预定义集成配置'
    )
    op.create_index(op.f('ix_integration_templates_id'), 'integration_templates', ['id'], unique=False)

    # Create api_documentation table
    op.create_table('api_documentation',
        sa.Column('id', sa.Integer(), nullable=False, comment='文档ID'),
        sa.Column('title', sa.String(length=255), nullable=False, comment='文档标题'),
        sa.Column('content', sa.Text(), nullable=False, comment='文档内容'),
        sa.Column('content_type', sa.String(length=50), nullable=False, comment='内容类型'),
        sa.Column('category', sa.String(length=100), nullable=True, comment='文档分类'),
        sa.Column('tags', sa.JSON(), nullable=True, comment='文档标签'),
        sa.Column('version', sa.String(length=20), nullable=False, comment='API版本'),
        sa.Column('order_index', sa.Integer(), nullable=True, comment='排序索引'),
        sa.Column('is_published', sa.Boolean(), nullable=True, comment='是否已发布'),
        sa.Column('is_featured', sa.Boolean(), nullable=True, comment='是否推荐'),
        sa.Column('view_count', sa.Integer(), nullable=True, comment='浏览次数'),
        sa.Column('last_viewed_at', sa.DateTime(), nullable=True, comment='最后浏览时间'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='API文档表，管理API文档内容'
    )
    op.create_index(op.f('ix_api_documentation_id'), 'api_documentation', ['id'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_api_documentation_id'), table_name='api_documentation')
    op.drop_table('api_documentation')
    
    op.drop_index(op.f('ix_integration_templates_id'), table_name='integration_templates')
    op.drop_table('integration_templates')
    
    op.drop_index(op.f('ix_api_usage_logs_created_at'), table_name='api_usage_logs')
    op.drop_index(op.f('ix_api_usage_logs_id'), table_name='api_usage_logs')
    op.drop_table('api_usage_logs')
    
    op.drop_index(op.f('ix_api_endpoints_id'), table_name='api_endpoints')
    op.drop_table('api_endpoints')
    
    op.drop_index(op.f('ix_integrations_id'), table_name='integrations')
    op.drop_table('integrations')
    
    op.drop_index(op.f('ix_webhook_deliveries_id'), table_name='webhook_deliveries')
    op.drop_table('webhook_deliveries')
    
    op.drop_index(op.f('ix_webhooks_id'), table_name='webhooks')
    op.drop_table('webhooks')
    
    op.drop_index(op.f('ix_api_keys_id'), table_name='api_keys')
    op.drop_table('api_keys')
