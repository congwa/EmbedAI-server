"""Add security management tables

Revision ID: 006
Revises: 005
Create Date: 2024-08-04 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    # Create two_factor_auth table
    op.create_table('two_factor_auth',
        sa.Column('id', sa.Integer(), nullable=False, comment='2FA ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('method', sa.String(length=20), nullable=False, comment='认证方法'),
        sa.Column('secret_key', sa.String(length=255), nullable=False, comment='密钥'),
        sa.Column('backup_codes', sa.JSON(), nullable=True, comment='备用验证码'),
        sa.Column('is_enabled', sa.Boolean(), nullable=True, comment='是否启用'),
        sa.Column('phone_number', sa.String(length=20), nullable=True, comment='手机号码'),
        sa.Column('email', sa.String(length=255), nullable=True, comment='邮箱地址'),
        sa.Column('last_used_at', sa.DateTime(), nullable=True, comment='最后使用时间'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
        comment='双因子认证表，存储用户的2FA设置'
    )
    op.create_index(op.f('ix_two_factor_auth_id'), 'two_factor_auth', ['id'], unique=False)

    # Create user_sessions_enhanced table
    op.create_table('user_sessions_enhanced',
        sa.Column('id', sa.Integer(), nullable=False, comment='会话ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('session_token', sa.String(length=255), nullable=False, comment='会话令牌'),
        sa.Column('refresh_token', sa.String(length=255), nullable=True, comment='刷新令牌'),
        sa.Column('ip_address', sa.String(length=45), nullable=True, comment='IP地址'),
        sa.Column('user_agent', sa.Text(), nullable=True, comment='用户代理'),
        sa.Column('device_fingerprint', sa.String(length=255), nullable=True, comment='设备指纹'),
        sa.Column('location', sa.JSON(), nullable=True, comment='地理位置信息'),
        sa.Column('status', sa.String(length=20), nullable=False, comment='会话状态'),
        sa.Column('is_mobile', sa.Boolean(), nullable=True, comment='是否移动设备'),
        sa.Column('is_trusted', sa.Boolean(), nullable=True, comment='是否受信任设备'),
        sa.Column('last_activity', sa.DateTime(), nullable=True, comment='最后活动时间'),
        sa.Column('expires_at', sa.DateTime(), nullable=False, comment='过期时间'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('terminated_at', sa.DateTime(), nullable=True, comment='终止时间'),
        sa.Column('terminated_by', sa.Integer(), nullable=True, comment='终止人'),
        sa.ForeignKeyConstraint(['terminated_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_token'),
        sa.UniqueConstraint('refresh_token'),
        comment='增强用户会话表，包含安全信息'
    )
    op.create_index(op.f('ix_user_sessions_enhanced_id'), 'user_sessions_enhanced', ['id'], unique=False)
    op.create_index(op.f('ix_user_sessions_enhanced_session_token'), 'user_sessions_enhanced', ['session_token'], unique=False)

    # Create ip_whitelist table
    op.create_table('ip_whitelist',
        sa.Column('id', sa.Integer(), nullable=False, comment='白名单ID'),
        sa.Column('ip_address', sa.String(length=45), nullable=False, comment='IP地址'),
        sa.Column('ip_range', sa.String(length=50), nullable=True, comment='IP范围(CIDR)'),
        sa.Column('description', sa.Text(), nullable=True, comment='描述'),
        sa.Column('user_id', sa.Integer(), nullable=True, comment='关联用户ID'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否激活'),
        sa.Column('expires_at', sa.DateTime(), nullable=True, comment='过期时间'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='IP白名单表，管理允许访问的IP地址'
    )
    op.create_index(op.f('ix_ip_whitelist_id'), 'ip_whitelist', ['id'], unique=False)

    # Create ip_blacklist table
    op.create_table('ip_blacklist',
        sa.Column('id', sa.Integer(), nullable=False, comment='黑名单ID'),
        sa.Column('ip_address', sa.String(length=45), nullable=False, comment='IP地址'),
        sa.Column('ip_range', sa.String(length=50), nullable=True, comment='IP范围(CIDR)'),
        sa.Column('reason', sa.Text(), nullable=True, comment='封禁原因'),
        sa.Column('block_type', sa.String(length=20), nullable=False, comment='封禁类型'),
        sa.Column('failed_attempts', sa.Integer(), nullable=True, comment='失败尝试次数'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否激活'),
        sa.Column('expires_at', sa.DateTime(), nullable=True, comment='过期时间'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='IP黑名单表，管理被禁止访问的IP地址'
    )
    op.create_index(op.f('ix_ip_blacklist_id'), 'ip_blacklist', ['id'], unique=False)

    # Create security_events table
    op.create_table('security_events',
        sa.Column('id', sa.Integer(), nullable=False, comment='事件ID'),
        sa.Column('user_id', sa.Integer(), nullable=True, comment='用户ID'),
        sa.Column('event_type', sa.String(length=50), nullable=False, comment='事件类型'),
        sa.Column('severity', sa.String(length=20), nullable=False, comment='严重程度'),
        sa.Column('ip_address', sa.String(length=45), nullable=True, comment='IP地址'),
        sa.Column('user_agent', sa.Text(), nullable=True, comment='用户代理'),
        sa.Column('session_id', sa.String(length=255), nullable=True, comment='会话ID'),
        sa.Column('details', sa.JSON(), nullable=True, comment='事件详情'),
        sa.Column('risk_score', sa.Integer(), nullable=True, comment='风险评分'),
        sa.Column('is_resolved', sa.Boolean(), nullable=True, comment='是否已处理'),
        sa.Column('resolved_at', sa.DateTime(), nullable=True, comment='处理时间'),
        sa.Column('resolved_by', sa.Integer(), nullable=True, comment='处理人'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='安全事件表，记录系统安全相关事件'
    )
    op.create_index(op.f('ix_security_events_id'), 'security_events', ['id'], unique=False)
    op.create_index(op.f('ix_security_events_created_at'), 'security_events', ['created_at'], unique=False)

    # Create password_history table
    op.create_table('password_history',
        sa.Column('id', sa.Integer(), nullable=False, comment='历史ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('password_hash', sa.String(length=255), nullable=False, comment='密码哈希'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='密码历史表，记录用户密码变更历史'
    )
    op.create_index(op.f('ix_password_history_id'), 'password_history', ['id'], unique=False)
    op.create_index(op.f('ix_password_history_created_at'), 'password_history', ['created_at'], unique=False)

    # Create device_fingerprints table
    op.create_table('device_fingerprints',
        sa.Column('id', sa.Integer(), nullable=False, comment='指纹ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('fingerprint_hash', sa.String(length=255), nullable=False, comment='指纹哈希'),
        sa.Column('device_info', sa.JSON(), nullable=True, comment='设备信息'),
        sa.Column('browser_info', sa.JSON(), nullable=True, comment='浏览器信息'),
        sa.Column('screen_resolution', sa.String(length=20), nullable=True, comment='屏幕分辨率'),
        sa.Column('timezone', sa.String(length=50), nullable=True, comment='时区'),
        sa.Column('language', sa.String(length=10), nullable=True, comment='语言'),
        sa.Column('is_trusted', sa.Boolean(), nullable=True, comment='是否受信任'),
        sa.Column('last_seen', sa.DateTime(), nullable=True, comment='最后见到时间'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('fingerprint_hash'),
        comment='设备指纹表，记录和识别用户设备'
    )
    op.create_index(op.f('ix_device_fingerprints_id'), 'device_fingerprints', ['id'], unique=False)

    # Create security_policies table
    op.create_table('security_policies',
        sa.Column('id', sa.Integer(), nullable=False, comment='策略ID'),
        sa.Column('name', sa.String(length=100), nullable=False, comment='策略名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='策略描述'),
        sa.Column('policy_type', sa.String(length=50), nullable=False, comment='策略类型'),
        sa.Column('rules', sa.JSON(), nullable=False, comment='策略规则'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否激活'),
        sa.Column('priority', sa.Integer(), nullable=True, comment='优先级'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        comment='安全策略表，定义系统安全策略和规则'
    )
    op.create_index(op.f('ix_security_policies_id'), 'security_policies', ['id'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_security_policies_id'), table_name='security_policies')
    op.drop_table('security_policies')
    
    op.drop_index(op.f('ix_device_fingerprints_id'), table_name='device_fingerprints')
    op.drop_table('device_fingerprints')
    
    op.drop_index(op.f('ix_password_history_created_at'), table_name='password_history')
    op.drop_index(op.f('ix_password_history_id'), table_name='password_history')
    op.drop_table('password_history')
    
    op.drop_index(op.f('ix_security_events_created_at'), table_name='security_events')
    op.drop_index(op.f('ix_security_events_id'), table_name='security_events')
    op.drop_table('security_events')
    
    op.drop_index(op.f('ix_ip_blacklist_id'), table_name='ip_blacklist')
    op.drop_table('ip_blacklist')
    
    op.drop_index(op.f('ix_ip_whitelist_id'), table_name='ip_whitelist')
    op.drop_table('ip_whitelist')
    
    op.drop_index(op.f('ix_user_sessions_enhanced_session_token'), table_name='user_sessions_enhanced')
    op.drop_index(op.f('ix_user_sessions_enhanced_id'), table_name='user_sessions_enhanced')
    op.drop_table('user_sessions_enhanced')
    
    op.drop_index(op.f('ix_two_factor_auth_id'), table_name='two_factor_auth')
    op.drop_table('two_factor_auth')
