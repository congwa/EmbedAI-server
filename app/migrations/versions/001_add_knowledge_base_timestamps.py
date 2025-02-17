"""添加知识库时间戳字段

Revision ID: 001
Revises: 
Create Date: 2024-03-19 10:00:00.000000

"""
from datetime import datetime
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # 添加created_at和updated_at字段
    now = datetime.now().isoformat()
    op.add_column('knowledge_bases', sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text(f"'{now}'")))
    op.add_column('knowledge_bases', sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text(f"'{now}'")))

def downgrade():
    # 删除created_at和updated_at字段
    op.drop_column('knowledge_bases', 'updated_at')
    op.drop_column('knowledge_bases', 'created_at') 