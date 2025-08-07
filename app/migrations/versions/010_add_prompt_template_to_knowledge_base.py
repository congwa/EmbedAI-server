"""add prompt template to knowledge base

Revision ID: 010_add_prompt_template_to_knowledge_base
Revises: 009_add_prompt_management_tables
Create Date: 2024-08-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010_add_prompt_template_to_knowledge_base'
down_revision = '009_add_prompt_management_tables'
branch_labels = None
depends_on = None


def upgrade():
    """添加提示词模板相关字段到知识库表"""
    # 添加默认提示词模板ID字段
    op.add_column('knowledge_bases', sa.Column(
        'default_prompt_template_id', 
        sa.Integer(), 
        nullable=True,
        comment='默认提示词模板ID'
    ))
    
    # 添加提示词模板配置字段
    op.add_column('knowledge_bases', sa.Column(
        'prompt_template_config', 
        sa.JSON(), 
        nullable=True,
        comment='提示词模板配置，包含模板选择策略和变量映射'
    ))
    
    # 创建外键约束
    op.create_foreign_key(
        'fk_knowledge_bases_default_prompt_template',
        'knowledge_bases', 
        'prompt_templates',
        ['default_prompt_template_id'], 
        ['id'],
        ondelete='SET NULL'
    )
    
    # 创建索引
    op.create_index(
        'ix_knowledge_bases_default_prompt_template_id',
        'knowledge_bases',
        ['default_prompt_template_id']
    )


def downgrade():
    """移除提示词模板相关字段"""
    # 删除索引
    op.drop_index('ix_knowledge_bases_default_prompt_template_id', table_name='knowledge_bases')
    
    # 删除外键约束
    op.drop_constraint('fk_knowledge_bases_default_prompt_template', 'knowledge_bases', type_='foreignkey')
    
    # 删除字段
    op.drop_column('knowledge_bases', 'prompt_template_config')
    op.drop_column('knowledge_bases', 'default_prompt_template_id')