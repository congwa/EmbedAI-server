"""Add analytics tables

Revision ID: 002_add_analytics_tables
Revises: 001_add_rag_support
Create Date: 2024-08-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Create system_metrics table
    op.create_table('system_metrics',
        sa.Column('id', sa.Integer(), nullable=False, comment='指标ID'),
        sa.Column('metric_type', sa.String(length=50), nullable=False, comment='指标类型'),
        sa.Column('metric_name', sa.String(length=100), nullable=False, comment='指标名称'),
        sa.Column('metric_value', sa.Float(), nullable=False, comment='指标值'),
        sa.Column('metric_unit', sa.String(length=20), nullable=True, comment='指标单位'),
        sa.Column('extra_metadata', sa.JSON(), nullable=True, comment='额外元数据'),
        sa.Column('timestamp', sa.DateTime(), nullable=True, comment='记录时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='系统指标表，存储系统性能和使用数据'
    )
    op.create_index(op.f('ix_system_metrics_id'), 'system_metrics', ['id'], unique=False)
    op.create_index(op.f('ix_system_metrics_metric_type'), 'system_metrics', ['metric_type'], unique=False)
    op.create_index(op.f('ix_system_metrics_timestamp'), 'system_metrics', ['timestamp'], unique=False)

    # Create user_activity_logs table
    op.create_table('user_activity_logs',
        sa.Column('id', sa.Integer(), nullable=False, comment='日志ID'),
        sa.Column('user_id', sa.Integer(), nullable=True, comment='用户ID'),
        sa.Column('session_id', sa.String(length=64), nullable=True, comment='会话ID'),
        sa.Column('activity_type', sa.String(length=50), nullable=False, comment='活动类型'),
        sa.Column('activity_details', sa.JSON(), nullable=True, comment='活动详情'),
        sa.Column('ip_address', sa.String(length=45), nullable=True, comment='IP地址'),
        sa.Column('user_agent', sa.String(length=500), nullable=True, comment='用户代理'),
        sa.Column('timestamp', sa.DateTime(), nullable=True, comment='活动时间'),
        sa.Column('duration', sa.Integer(), nullable=True, comment='持续时间(秒)'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='用户活动日志表，记录用户行为和会话信息'
    )
    op.create_index(op.f('ix_user_activity_logs_id'), 'user_activity_logs', ['id'], unique=False)
    op.create_index(op.f('ix_user_activity_logs_session_id'), 'user_activity_logs', ['session_id'], unique=False)
    op.create_index(op.f('ix_user_activity_logs_activity_type'), 'user_activity_logs', ['activity_type'], unique=False)
    op.create_index(op.f('ix_user_activity_logs_timestamp'), 'user_activity_logs', ['timestamp'], unique=False)

    # Create knowledge_base_metrics table
    op.create_table('knowledge_base_metrics',
        sa.Column('id', sa.Integer(), nullable=False, comment='指标ID'),
        sa.Column('knowledge_base_id', sa.Integer(), nullable=False, comment='知识库ID'),
        sa.Column('metric_date', sa.DateTime(), nullable=False, comment='指标日期'),
        sa.Column('query_count', sa.Integer(), nullable=True, comment='查询次数'),
        sa.Column('success_count', sa.Integer(), nullable=True, comment='成功次数'),
        sa.Column('error_count', sa.Integer(), nullable=True, comment='错误次数'),
        sa.Column('avg_response_time', sa.Float(), nullable=True, comment='平均响应时间(秒)'),
        sa.Column('total_tokens_used', sa.Integer(), nullable=True, comment='总Token使用量'),
        sa.Column('total_cost', sa.Float(), nullable=True, comment='总费用'),
        sa.Column('unique_users', sa.Integer(), nullable=True, comment='独立用户数'),
        sa.ForeignKeyConstraint(['knowledge_base_id'], ['knowledge_bases.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='知识库指标表，存储知识库使用统计'
    )
    op.create_index(op.f('ix_knowledge_base_metrics_id'), 'knowledge_base_metrics', ['id'], unique=False)
    op.create_index(op.f('ix_knowledge_base_metrics_metric_date'), 'knowledge_base_metrics', ['metric_date'], unique=False)

    # Create api_metrics table
    op.create_table('api_metrics',
        sa.Column('id', sa.Integer(), nullable=False, comment='指标ID'),
        sa.Column('endpoint', sa.String(length=200), nullable=False, comment='API端点'),
        sa.Column('method', sa.String(length=10), nullable=False, comment='HTTP方法'),
        sa.Column('status_code', sa.Integer(), nullable=False, comment='状态码'),
        sa.Column('response_time', sa.Float(), nullable=False, comment='响应时间(秒)'),
        sa.Column('user_id', sa.Integer(), nullable=True, comment='用户ID'),
        sa.Column('ip_address', sa.String(length=45), nullable=True, comment='IP地址'),
        sa.Column('timestamp', sa.DateTime(), nullable=True, comment='调用时间'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='API指标表，存储API调用统计'
    )
    op.create_index(op.f('ix_api_metrics_id'), 'api_metrics', ['id'], unique=False)
    op.create_index(op.f('ix_api_metrics_endpoint'), 'api_metrics', ['endpoint'], unique=False)
    op.create_index(op.f('ix_api_metrics_timestamp'), 'api_metrics', ['timestamp'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_api_metrics_timestamp'), table_name='api_metrics')
    op.drop_index(op.f('ix_api_metrics_endpoint'), table_name='api_metrics')
    op.drop_index(op.f('ix_api_metrics_id'), table_name='api_metrics')
    op.drop_table('api_metrics')
    
    op.drop_index(op.f('ix_knowledge_base_metrics_metric_date'), table_name='knowledge_base_metrics')
    op.drop_index(op.f('ix_knowledge_base_metrics_id'), table_name='knowledge_base_metrics')
    op.drop_table('knowledge_base_metrics')
    
    op.drop_index(op.f('ix_user_activity_logs_timestamp'), table_name='user_activity_logs')
    op.drop_index(op.f('ix_user_activity_logs_activity_type'), table_name='user_activity_logs')
    op.drop_index(op.f('ix_user_activity_logs_session_id'), table_name='user_activity_logs')
    op.drop_index(op.f('ix_user_activity_logs_id'), table_name='user_activity_logs')
    op.drop_table('user_activity_logs')
    
    op.drop_index(op.f('ix_system_metrics_timestamp'), table_name='system_metrics')
    op.drop_index(op.f('ix_system_metrics_metric_type'), table_name='system_metrics')
    op.drop_index(op.f('ix_system_metrics_id'), table_name='system_metrics')
    op.drop_table('system_metrics')
