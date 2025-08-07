"""Add prompt management tables

Revision ID: 009
Revises: 008
Create Date: 2024-08-07 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade():
    # Create prompt_categories table
    op.create_table('prompt_categories',
        sa.Column('id', sa.Integer(), nullable=False, comment='分类ID'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='分类名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='分类描述'),
        sa.Column('parent_id', sa.Integer(), nullable=True, comment='父分类ID'),
        sa.Column('sort_order', sa.Integer(), nullable=True, comment='排序顺序'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否激活状态'),
        sa.Column('template_count', sa.Integer(), nullable=True, comment='该分类下的模板数量'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.ForeignKeyConstraint(['parent_id'], ['prompt_categories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='提示词分类表，用于组织提示词模板的层级分类'
    )
    op.create_index(op.f('ix_prompt_categories_id'), 'prompt_categories', ['id'], unique=False)
    op.create_index(op.f('ix_prompt_categories_parent_id'), 'prompt_categories', ['parent_id'], unique=False)

    # Create prompt_templates table
    op.create_table('prompt_templates',
        sa.Column('id', sa.Integer(), nullable=False, comment='提示词模板ID'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='模板名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='模板描述'),
        sa.Column('category_id', sa.Integer(), nullable=True, comment='分类ID'),
        sa.Column('content', sa.Text(), nullable=False, comment='提示词内容，支持变量占位符'),
        sa.Column('variables', sa.JSON(), nullable=True, comment='变量定义，包含变量名、类型、默认值等'),
        sa.Column('tags', sa.JSON(), nullable=True, comment='标签列表，用于分类和搜索'),
        sa.Column('is_system', sa.Boolean(), nullable=True, comment='是否为系统内置模板'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否激活状态'),
        sa.Column('owner_id', sa.Integer(), nullable=False, comment='模板所有者用户ID'),
        sa.Column('usage_count', sa.Integer(), nullable=True, comment='使用次数统计'),
        sa.Column('last_used_at', sa.DateTime(), nullable=True, comment='最后使用时间'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.ForeignKeyConstraint(['category_id'], ['prompt_categories.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='提示词模板表，存储提示词模板的基本信息和内容'
    )
    op.create_index(op.f('ix_prompt_templates_id'), 'prompt_templates', ['id'], unique=False)
    op.create_index(op.f('ix_prompt_templates_name'), 'prompt_templates', ['name'], unique=False)
    op.create_index(op.f('ix_prompt_templates_owner_id'), 'prompt_templates', ['owner_id'], unique=False)
    op.create_index(op.f('ix_prompt_templates_category_id'), 'prompt_templates', ['category_id'], unique=False)
    op.create_index(op.f('ix_prompt_templates_is_active'), 'prompt_templates', ['is_active'], unique=False)

    # Create prompt_versions table
    op.create_table('prompt_versions',
        sa.Column('id', sa.Integer(), nullable=False, comment='版本ID'),
        sa.Column('template_id', sa.Integer(), nullable=False, comment='模板ID'),
        sa.Column('version_number', sa.String(length=50), nullable=False, comment='版本号，如v1.0.0'),
        sa.Column('content', sa.Text(), nullable=False, comment='该版本的提示词内容'),
        sa.Column('variables', sa.JSON(), nullable=True, comment='该版本的变量定义'),
        sa.Column('change_log', sa.Text(), nullable=True, comment='版本变更说明'),
        sa.Column('is_published', sa.Boolean(), nullable=True, comment='是否已发布'),
        sa.Column('is_current', sa.Boolean(), nullable=True, comment='是否为当前使用版本'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='版本创建者'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('published_at', sa.DateTime(), nullable=True, comment='发布时间'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['template_id'], ['prompt_templates.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='提示词版本表，用于管理提示词模板的版本控制'
    )
    op.create_index(op.f('ix_prompt_versions_id'), 'prompt_versions', ['id'], unique=False)
    op.create_index(op.f('ix_prompt_versions_template_id'), 'prompt_versions', ['template_id'], unique=False)
    op.create_index(op.f('ix_prompt_versions_is_current'), 'prompt_versions', ['is_current'], unique=False)

    # Create prompt_usage_logs table
    op.create_table('prompt_usage_logs',
        sa.Column('id', sa.Integer(), nullable=False, comment='日志ID'),
        sa.Column('template_id', sa.Integer(), nullable=False, comment='模板ID'),
        sa.Column('version_id', sa.Integer(), nullable=True, comment='使用的版本ID'),
        sa.Column('user_id', sa.Integer(), nullable=True, comment='使用者用户ID'),
        sa.Column('kb_id', sa.Integer(), nullable=True, comment='关联的知识库ID'),
        sa.Column('query', sa.Text(), nullable=True, comment='用户查询内容'),
        sa.Column('variables_used', sa.JSON(), nullable=True, comment='实际使用的变量值'),
        sa.Column('rendered_content', sa.Text(), nullable=True, comment='渲染后的完整提示词内容'),
        sa.Column('response_quality', sa.Float(), nullable=True, comment='响应质量评分（0-1）'),
        sa.Column('execution_time', sa.Float(), nullable=True, comment='执行时间（秒）'),
        sa.Column('token_count', sa.Integer(), nullable=True, comment='生成的token数量'),
        sa.Column('cost', sa.Float(), nullable=True, comment='使用成本（美元）'),
        sa.Column('success', sa.Boolean(), nullable=True, comment='是否执行成功'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息（如果失败）'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='使用时间'),
        sa.ForeignKeyConstraint(['kb_id'], ['knowledge_bases.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['template_id'], ['prompt_templates.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['version_id'], ['prompt_versions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='提示词使用日志表，记录提示词模板的使用情况和性能统计'
    )
    op.create_index(op.f('ix_prompt_usage_logs_id'), 'prompt_usage_logs', ['id'], unique=False)
    op.create_index(op.f('ix_prompt_usage_logs_template_id'), 'prompt_usage_logs', ['template_id'], unique=False)
    op.create_index(op.f('ix_prompt_usage_logs_created_at'), 'prompt_usage_logs', ['created_at'], unique=False)
    op.create_index(op.f('ix_prompt_usage_logs_user_id'), 'prompt_usage_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_prompt_usage_logs_kb_id'), 'prompt_usage_logs', ['kb_id'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_prompt_usage_logs_kb_id'), table_name='prompt_usage_logs')
    op.drop_index(op.f('ix_prompt_usage_logs_user_id'), table_name='prompt_usage_logs')
    op.drop_index(op.f('ix_prompt_usage_logs_created_at'), table_name='prompt_usage_logs')
    op.drop_index(op.f('ix_prompt_usage_logs_template_id'), table_name='prompt_usage_logs')
    op.drop_index(op.f('ix_prompt_usage_logs_id'), table_name='prompt_usage_logs')
    op.drop_table('prompt_usage_logs')
    
    op.drop_index(op.f('ix_prompt_versions_is_current'), table_name='prompt_versions')
    op.drop_index(op.f('ix_prompt_versions_template_id'), table_name='prompt_versions')
    op.drop_index(op.f('ix_prompt_versions_id'), table_name='prompt_versions')
    op.drop_table('prompt_versions')
    
    op.drop_index(op.f('ix_prompt_templates_is_active'), table_name='prompt_templates')
    op.drop_index(op.f('ix_prompt_templates_category_id'), table_name='prompt_templates')
    op.drop_index(op.f('ix_prompt_templates_owner_id'), table_name='prompt_templates')
    op.drop_index(op.f('ix_prompt_templates_name'), table_name='prompt_templates')
    op.drop_index(op.f('ix_prompt_templates_id'), table_name='prompt_templates')
    op.drop_table('prompt_templates')
    
    op.drop_index(op.f('ix_prompt_categories_parent_id'), table_name='prompt_categories')
    op.drop_index(op.f('ix_prompt_categories_id'), table_name='prompt_categories')
    op.drop_table('prompt_categories')