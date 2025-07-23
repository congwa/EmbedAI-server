"""添加RAG支持

Revision ID: 001
Revises: 
Create Date: 2025-07-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 为KnowledgeBase表添加RAG相关字段
    op.add_column('knowledge_bases', sa.Column('indexing_technique', sa.String(), nullable=False, server_default='high_quality', comment='索引技术（high_quality或economy）'))
    op.add_column('knowledge_bases', sa.Column('embedding_model', sa.String(), nullable=True, comment='嵌入模型名称'))
    op.add_column('knowledge_bases', sa.Column('embedding_model_provider', sa.String(), nullable=True, comment='嵌入模型提供商'))
    op.add_column('knowledge_bases', sa.Column('vector_store_type', sa.String(), nullable=True, comment='向量存储类型'))
    
    # 创建document_chunks表
    op.create_table('document_chunks',
        sa.Column('id', sa.Integer(), nullable=False, comment='分块ID'),
        sa.Column('document_id', sa.Integer(), nullable=False, comment='文档ID'),
        sa.Column('content', sa.Text(), nullable=False, comment='分块内容'),
        sa.Column('chunk_index', sa.Integer(), nullable=False, comment='分块索引'),
        sa.Column('metadata', sa.JSON(), nullable=True, comment='分块元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='更新时间'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='文档分块表，存储文档分块信息'
    )
    op.create_index(op.f('ix_document_chunks_id'), 'document_chunks', ['id'], unique=False)
    
    # 创建document_embeddings表
    op.create_table('document_embeddings',
        sa.Column('id', sa.Integer(), nullable=False, comment='向量ID'),
        sa.Column('chunk_id', sa.Integer(), nullable=False, comment='分块ID'),
        sa.Column('embedding', sa.JSON(), nullable=False, comment='向量数据'),
        sa.Column('model', sa.String(), nullable=False, comment='嵌入模型'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='创建时间'),
        sa.ForeignKeyConstraint(['chunk_id'], ['document_chunks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='文档向量表，存储文档向量信息'
    )
    op.create_index(op.f('ix_document_embeddings_id'), 'document_embeddings', ['id'], unique=False)


def downgrade():
    # 删除表
    op.drop_table('document_embeddings')
    op.drop_table('document_chunks')
    
    # 删除KnowledgeBase表中的RAG相关字段
    op.drop_column('knowledge_bases', 'vector_store_type')
    op.drop_column('knowledge_bases', 'embedding_model_provider')
    op.drop_column('knowledge_bases', 'embedding_model')
    op.drop_column('knowledge_bases', 'indexing_technique')