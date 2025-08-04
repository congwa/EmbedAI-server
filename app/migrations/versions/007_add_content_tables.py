"""Add content management tables

Revision ID: 007
Revises: 006
Create Date: 2024-08-04 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    # Create content_moderation_rules table
    op.create_table('content_moderation_rules',
        sa.Column('id', sa.Integer(), nullable=False, comment='规则ID'),
        sa.Column('name', sa.String(length=100), nullable=False, comment='规则名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='规则描述'),
        sa.Column('rule_type', sa.String(length=50), nullable=False, comment='规则类型'),
        sa.Column('conditions', sa.JSON(), nullable=False, comment='规则条件'),
        sa.Column('actions', sa.JSON(), nullable=False, comment='执行动作'),
        sa.Column('priority', sa.Integer(), nullable=True, comment='优先级'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否激活'),
        sa.Column('auto_apply', sa.Boolean(), nullable=True, comment='是否自动应用'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='内容审核规则表，定义自动审核规则'
    )
    op.create_index(op.f('ix_content_moderation_rules_id'), 'content_moderation_rules', ['id'], unique=False)

    # Create content_moderation_logs table
    op.create_table('content_moderation_logs',
        sa.Column('id', sa.Integer(), nullable=False, comment='日志ID'),
        sa.Column('content_type', sa.String(length=50), nullable=False, comment='内容类型'),
        sa.Column('content_id', sa.Integer(), nullable=False, comment='内容ID'),
        sa.Column('rule_id', sa.Integer(), nullable=True, comment='规则ID'),
        sa.Column('moderator_id', sa.Integer(), nullable=True, comment='审核员ID'),
        sa.Column('action', sa.String(length=20), nullable=False, comment='审核动作'),
        sa.Column('reason', sa.Text(), nullable=True, comment='审核原因'),
        sa.Column('details', sa.JSON(), nullable=True, comment='审核详情'),
        sa.Column('confidence_score', sa.Float(), nullable=True, comment='置信度分数'),
        sa.Column('is_automated', sa.Boolean(), nullable=True, comment='是否自动审核'),
        sa.Column('previous_status', sa.String(length=20), nullable=True, comment='之前状态'),
        sa.Column('new_status', sa.String(length=20), nullable=True, comment='新状态'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.ForeignKeyConstraint(['moderator_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['rule_id'], ['content_moderation_rules.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='内容审核日志表，记录审核历史'
    )
    op.create_index(op.f('ix_content_moderation_logs_id'), 'content_moderation_logs', ['id'], unique=False)
    op.create_index(op.f('ix_content_moderation_logs_created_at'), 'content_moderation_logs', ['created_at'], unique=False)

    # Create bulk_operations table
    op.create_table('bulk_operations',
        sa.Column('id', sa.Integer(), nullable=False, comment='操作ID'),
        sa.Column('name', sa.String(length=100), nullable=False, comment='操作名称'),
        sa.Column('operation_type', sa.String(length=50), nullable=False, comment='操作类型'),
        sa.Column('target_type', sa.String(length=50), nullable=False, comment='目标类型'),
        sa.Column('target_ids', sa.JSON(), nullable=False, comment='目标ID列表'),
        sa.Column('parameters', sa.JSON(), nullable=True, comment='操作参数'),
        sa.Column('status', sa.String(length=20), nullable=False, comment='操作状态'),
        sa.Column('progress', sa.Integer(), nullable=True, comment='进度百分比'),
        sa.Column('total_items', sa.Integer(), nullable=False, comment='总项目数'),
        sa.Column('processed_items', sa.Integer(), nullable=True, comment='已处理项目数'),
        sa.Column('success_items', sa.Integer(), nullable=True, comment='成功项目数'),
        sa.Column('failed_items', sa.Integer(), nullable=True, comment='失败项目数'),
        sa.Column('error_details', sa.JSON(), nullable=True, comment='错误详情'),
        sa.Column('result_data', sa.JSON(), nullable=True, comment='结果数据'),
        sa.Column('started_at', sa.DateTime(), nullable=True, comment='开始时间'),
        sa.Column('completed_at', sa.DateTime(), nullable=True, comment='完成时间'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='批量操作表，记录批量操作任务'
    )
    op.create_index(op.f('ix_bulk_operations_id'), 'bulk_operations', ['id'], unique=False)

    # Create content_tags table
    op.create_table('content_tags',
        sa.Column('id', sa.Integer(), nullable=False, comment='标签ID'),
        sa.Column('name', sa.String(length=50), nullable=False, comment='标签名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='标签描述'),
        sa.Column('color', sa.String(length=7), nullable=True, comment='标签颜色'),
        sa.Column('category', sa.String(length=50), nullable=True, comment='标签分类'),
        sa.Column('usage_count', sa.Integer(), nullable=True, comment='使用次数'),
        sa.Column('is_system', sa.Boolean(), nullable=True, comment='是否系统标签'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否激活'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        comment='内容标签表，管理标签系统'
    )
    op.create_index(op.f('ix_content_tags_id'), 'content_tags', ['id'], unique=False)

    # Create content_categories table
    op.create_table('content_categories',
        sa.Column('id', sa.Integer(), nullable=False, comment='分类ID'),
        sa.Column('name', sa.String(length=100), nullable=False, comment='分类名称'),
        sa.Column('slug', sa.String(length=100), nullable=False, comment='分类标识'),
        sa.Column('description', sa.Text(), nullable=True, comment='分类描述'),
        sa.Column('parent_id', sa.Integer(), nullable=True, comment='父分类ID'),
        sa.Column('level', sa.Integer(), nullable=True, comment='分类层级'),
        sa.Column('sort_order', sa.Integer(), nullable=True, comment='排序顺序'),
        sa.Column('icon', sa.String(length=50), nullable=True, comment='分类图标'),
        sa.Column('color', sa.String(length=7), nullable=True, comment='分类颜色'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否激活'),
        sa.Column('content_count', sa.Integer(), nullable=True, comment='内容数量'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['parent_id'], ['content_categories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
        comment='内容分类表，管理分类系统'
    )
    op.create_index(op.f('ix_content_categories_id'), 'content_categories', ['id'], unique=False)

    # Create search_indexes table
    op.create_table('search_indexes',
        sa.Column('id', sa.Integer(), nullable=False, comment='索引ID'),
        sa.Column('content_type', sa.String(length=50), nullable=False, comment='内容类型'),
        sa.Column('content_id', sa.Integer(), nullable=False, comment='内容ID'),
        sa.Column('title', sa.String(length=255), nullable=True, comment='标题'),
        sa.Column('content', sa.Text(), nullable=True, comment='内容'),
        sa.Column('keywords', sa.Text(), nullable=True, comment='关键词'),
        sa.Column('meta_data', sa.JSON(), nullable=True, comment='元数据'),
        sa.Column('language', sa.String(length=10), nullable=True, comment='语言'),
        sa.Column('search_vector', sa.Text(), nullable=True, comment='搜索向量'),
        sa.Column('boost_score', sa.Float(), nullable=True, comment='权重分数'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否激活'),
        sa.Column('last_indexed', sa.DateTime(), nullable=True, comment='最后索引时间'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='搜索索引表，管理全文搜索'
    )
    op.create_index(op.f('ix_search_indexes_id'), 'search_indexes', ['id'], unique=False)

    # Create content_statistics table
    op.create_table('content_statistics',
        sa.Column('id', sa.Integer(), nullable=False, comment='统计ID'),
        sa.Column('date', sa.DateTime(), nullable=False, comment='统计日期'),
        sa.Column('content_type', sa.String(length=50), nullable=False, comment='内容类型'),
        sa.Column('total_count', sa.Integer(), nullable=True, comment='总数量'),
        sa.Column('published_count', sa.Integer(), nullable=True, comment='已发布数量'),
        sa.Column('draft_count', sa.Integer(), nullable=True, comment='草稿数量'),
        sa.Column('pending_count', sa.Integer(), nullable=True, comment='待审核数量'),
        sa.Column('approved_count', sa.Integer(), nullable=True, comment='已批准数量'),
        sa.Column('rejected_count', sa.Integer(), nullable=True, comment='已拒绝数量'),
        sa.Column('archived_count', sa.Integer(), nullable=True, comment='已归档数量'),
        sa.Column('deleted_count', sa.Integer(), nullable=True, comment='已删除数量'),
        sa.Column('views_count', sa.Integer(), nullable=True, comment='浏览次数'),
        sa.Column('downloads_count', sa.Integer(), nullable=True, comment='下载次数'),
        sa.Column('shares_count', sa.Integer(), nullable=True, comment='分享次数'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='内容统计表，记录统计数据'
    )
    op.create_index(op.f('ix_content_statistics_id'), 'content_statistics', ['id'], unique=False)

    # Create data_export_tasks table
    op.create_table('data_export_tasks',
        sa.Column('id', sa.Integer(), nullable=False, comment='任务ID'),
        sa.Column('name', sa.String(length=100), nullable=False, comment='任务名称'),
        sa.Column('export_type', sa.String(length=50), nullable=False, comment='导出类型'),
        sa.Column('data_type', sa.String(length=50), nullable=False, comment='数据类型'),
        sa.Column('filters', sa.JSON(), nullable=True, comment='过滤条件'),
        sa.Column('format', sa.String(length=20), nullable=False, comment='导出格式'),
        sa.Column('status', sa.String(length=20), nullable=False, comment='任务状态'),
        sa.Column('progress', sa.Integer(), nullable=True, comment='进度百分比'),
        sa.Column('total_records', sa.Integer(), nullable=True, comment='总记录数'),
        sa.Column('exported_records', sa.Integer(), nullable=True, comment='已导出记录数'),
        sa.Column('file_path', sa.String(length=255), nullable=True, comment='文件路径'),
        sa.Column('file_size', sa.Integer(), nullable=True, comment='文件大小'),
        sa.Column('download_url', sa.String(length=255), nullable=True, comment='下载链接'),
        sa.Column('expires_at', sa.DateTime(), nullable=True, comment='过期时间'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息'),
        sa.Column('started_at', sa.DateTime(), nullable=True, comment='开始时间'),
        sa.Column('completed_at', sa.DateTime(), nullable=True, comment='完成时间'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='数据导出任务表，管理导出任务'
    )
    op.create_index(op.f('ix_data_export_tasks_id'), 'data_export_tasks', ['id'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_data_export_tasks_id'), table_name='data_export_tasks')
    op.drop_table('data_export_tasks')
    
    op.drop_index(op.f('ix_content_statistics_id'), table_name='content_statistics')
    op.drop_table('content_statistics')
    
    op.drop_index(op.f('ix_search_indexes_id'), table_name='search_indexes')
    op.drop_table('search_indexes')
    
    op.drop_index(op.f('ix_content_categories_id'), table_name='content_categories')
    op.drop_table('content_categories')
    
    op.drop_index(op.f('ix_content_tags_id'), table_name='content_tags')
    op.drop_table('content_tags')
    
    op.drop_index(op.f('ix_bulk_operations_id'), table_name='bulk_operations')
    op.drop_table('bulk_operations')
    
    op.drop_index(op.f('ix_content_moderation_logs_created_at'), table_name='content_moderation_logs')
    op.drop_index(op.f('ix_content_moderation_logs_id'), table_name='content_moderation_logs')
    op.drop_table('content_moderation_logs')
    
    op.drop_index(op.f('ix_content_moderation_rules_id'), table_name='content_moderation_rules')
    op.drop_table('content_moderation_rules')
