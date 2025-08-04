"""Add health monitoring tables

Revision ID: 003
Revises: 002
Create Date: 2024-08-04 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Create service_health table
    op.create_table('service_health',
        sa.Column('id', sa.Integer(), nullable=False, comment='健康检查ID'),
        sa.Column('service_name', sa.String(length=100), nullable=False, comment='服务名称'),
        sa.Column('service_type', sa.String(length=50), nullable=False, comment='服务类型'),
        sa.Column('status', sa.String(length=20), nullable=False, comment='健康状态'),
        sa.Column('response_time', sa.Float(), nullable=True, comment='响应时间(毫秒)'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息'),
        sa.Column('details', sa.JSON(), nullable=True, comment='详细信息'),
        sa.Column('timestamp', sa.DateTime(), nullable=True, comment='检查时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='服务健康状态表，存储各服务组件的健康检查结果'
    )
    op.create_index(op.f('ix_service_health_id'), 'service_health', ['id'], unique=False)
    op.create_index(op.f('ix_service_health_service_name'), 'service_health', ['service_name'], unique=False)
    op.create_index(op.f('ix_service_health_timestamp'), 'service_health', ['timestamp'], unique=False)

    # Create system_alerts table
    op.create_table('system_alerts',
        sa.Column('id', sa.Integer(), nullable=False, comment='警告ID'),
        sa.Column('alert_type', sa.String(length=50), nullable=False, comment='警告类型'),
        sa.Column('level', sa.String(length=20), nullable=False, comment='警告级别'),
        sa.Column('title', sa.String(length=200), nullable=False, comment='警告标题'),
        sa.Column('message', sa.Text(), nullable=False, comment='警告消息'),
        sa.Column('source', sa.String(length=100), nullable=True, comment='警告来源'),
        sa.Column('alert_metadata', sa.JSON(), nullable=True, comment='警告元数据'),
        sa.Column('is_resolved', sa.Boolean(), nullable=True, comment='是否已解决'),
        sa.Column('resolved_at', sa.DateTime(), nullable=True, comment='解决时间'),
        sa.Column('resolved_by', sa.String(length=100), nullable=True, comment='解决人'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='系统警告表，存储系统警告和通知信息'
    )
    op.create_index(op.f('ix_system_alerts_id'), 'system_alerts', ['id'], unique=False)
    op.create_index(op.f('ix_system_alerts_alert_type'), 'system_alerts', ['alert_type'], unique=False)
    op.create_index(op.f('ix_system_alerts_created_at'), 'system_alerts', ['created_at'], unique=False)

    # Create performance_thresholds table
    op.create_table('performance_thresholds',
        sa.Column('id', sa.Integer(), nullable=False, comment='阈值ID'),
        sa.Column('metric_name', sa.String(length=100), nullable=False, comment='指标名称'),
        sa.Column('metric_type', sa.String(length=50), nullable=False, comment='指标类型'),
        sa.Column('warning_threshold', sa.Float(), nullable=True, comment='警告阈值'),
        sa.Column('critical_threshold', sa.Float(), nullable=True, comment='严重阈值'),
        sa.Column('comparison_operator', sa.String(length=10), nullable=False, comment='比较操作符'),
        sa.Column('unit', sa.String(length=20), nullable=True, comment='单位'),
        sa.Column('description', sa.Text(), nullable=True, comment='描述'),
        sa.Column('is_enabled', sa.Boolean(), nullable=True, comment='是否启用'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('metric_name'),
        comment='性能阈值表，定义各种性能指标的警告阈值'
    )
    op.create_index(op.f('ix_performance_thresholds_id'), 'performance_thresholds', ['id'], unique=False)

    # Create health_check_configs table
    op.create_table('health_check_configs',
        sa.Column('id', sa.Integer(), nullable=False, comment='配置ID'),
        sa.Column('service_name', sa.String(length=100), nullable=False, comment='服务名称'),
        sa.Column('service_type', sa.String(length=50), nullable=False, comment='服务类型'),
        sa.Column('check_interval', sa.Integer(), nullable=False, comment='检查间隔(秒)'),
        sa.Column('timeout', sa.Integer(), nullable=False, comment='超时时间(秒)'),
        sa.Column('retry_count', sa.Integer(), nullable=False, comment='重试次数'),
        sa.Column('is_enabled', sa.Boolean(), nullable=True, comment='是否启用'),
        sa.Column('check_url', sa.String(length=500), nullable=True, comment='检查URL'),
        sa.Column('check_command', sa.String(length=500), nullable=True, comment='检查命令'),
        sa.Column('expected_response', sa.String(length=200), nullable=True, comment='期望响应'),
        sa.Column('config_data', sa.JSON(), nullable=True, comment='额外配置数据'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('service_name'),
        comment='健康检查配置表，存储健康检查的配置参数'
    )
    op.create_index(op.f('ix_health_check_configs_id'), 'health_check_configs', ['id'], unique=False)

    # Create uptime_records table
    op.create_table('uptime_records',
        sa.Column('id', sa.Integer(), nullable=False, comment='记录ID'),
        sa.Column('service_name', sa.String(length=100), nullable=False, comment='服务名称'),
        sa.Column('date', sa.DateTime(), nullable=False, comment='日期'),
        sa.Column('total_checks', sa.Integer(), nullable=False, comment='总检查次数'),
        sa.Column('successful_checks', sa.Integer(), nullable=False, comment='成功检查次数'),
        sa.Column('failed_checks', sa.Integer(), nullable=False, comment='失败检查次数'),
        sa.Column('uptime_percentage', sa.Float(), nullable=False, comment='运行时间百分比'),
        sa.Column('avg_response_time', sa.Float(), nullable=True, comment='平均响应时间(毫秒)'),
        sa.Column('max_response_time', sa.Float(), nullable=True, comment='最大响应时间(毫秒)'),
        sa.Column('min_response_time', sa.Float(), nullable=True, comment='最小响应时间(毫秒)'),
        sa.Column('downtime_duration', sa.Integer(), nullable=False, comment='停机时长(秒)'),
        sa.PrimaryKeyConstraint('id'),
        comment='运行时间记录表，存储系统和服务的运行时间统计'
    )
    op.create_index(op.f('ix_uptime_records_id'), 'uptime_records', ['id'], unique=False)
    op.create_index(op.f('ix_uptime_records_service_name'), 'uptime_records', ['service_name'], unique=False)
    op.create_index(op.f('ix_uptime_records_date'), 'uptime_records', ['date'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_uptime_records_date'), table_name='uptime_records')
    op.drop_index(op.f('ix_uptime_records_service_name'), table_name='uptime_records')
    op.drop_index(op.f('ix_uptime_records_id'), table_name='uptime_records')
    op.drop_table('uptime_records')
    
    op.drop_index(op.f('ix_health_check_configs_id'), table_name='health_check_configs')
    op.drop_table('health_check_configs')
    
    op.drop_index(op.f('ix_performance_thresholds_id'), table_name='performance_thresholds')
    op.drop_table('performance_thresholds')
    
    op.drop_index(op.f('ix_system_alerts_created_at'), table_name='system_alerts')
    op.drop_index(op.f('ix_system_alerts_alert_type'), table_name='system_alerts')
    op.drop_index(op.f('ix_system_alerts_id'), table_name='system_alerts')
    op.drop_table('system_alerts')
    
    op.drop_index(op.f('ix_service_health_timestamp'), table_name='service_health')
    op.drop_index(op.f('ix_service_health_service_name'), table_name='service_health')
    op.drop_index(op.f('ix_service_health_id'), table_name='service_health')
    op.drop_table('service_health')
