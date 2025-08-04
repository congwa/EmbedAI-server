"""Add RBAC tables

Revision ID: 004
Revises: 003
Create Date: 2024-08-04 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Create permissions table
    op.create_table('permissions',
        sa.Column('id', sa.Integer(), nullable=False, comment='权限ID'),
        sa.Column('name', sa.String(length=100), nullable=False, comment='权限名称'),
        sa.Column('code', sa.String(length=100), nullable=False, comment='权限代码'),
        sa.Column('description', sa.Text(), nullable=True, comment='权限描述'),
        sa.Column('resource', sa.String(length=100), nullable=False, comment='资源类型'),
        sa.Column('action', sa.String(length=50), nullable=False, comment='操作类型'),
        sa.Column('is_system', sa.Boolean(), nullable=True, comment='是否为系统权限'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否激活'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('code'),
        comment='权限表，定义系统中的各种权限'
    )
    op.create_index(op.f('ix_permissions_id'), 'permissions', ['id'], unique=False)

    # Create roles table
    op.create_table('roles',
        sa.Column('id', sa.Integer(), nullable=False, comment='角色ID'),
        sa.Column('name', sa.String(length=100), nullable=False, comment='角色名称'),
        sa.Column('code', sa.String(length=100), nullable=False, comment='角色代码'),
        sa.Column('description', sa.Text(), nullable=True, comment='角色描述'),
        sa.Column('is_system', sa.Boolean(), nullable=True, comment='是否为系统角色'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否激活'),
        sa.Column('priority', sa.Integer(), nullable=True, comment='角色优先级'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('code'),
        comment='角色表，定义用户角色和权限组合'
    )
    op.create_index(op.f('ix_roles_id'), 'roles', ['id'], unique=False)

    # Create user_groups table
    op.create_table('user_groups',
        sa.Column('id', sa.Integer(), nullable=False, comment='用户组ID'),
        sa.Column('name', sa.String(length=100), nullable=False, comment='用户组名称'),
        sa.Column('code', sa.String(length=100), nullable=False, comment='用户组代码'),
        sa.Column('description', sa.Text(), nullable=True, comment='用户组描述'),
        sa.Column('parent_id', sa.Integer(), nullable=True, comment='父用户组ID'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否激活'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['parent_id'], ['user_groups.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('code'),
        comment='用户组表，用于组织和管理用户'
    )
    op.create_index(op.f('ix_user_groups_id'), 'user_groups', ['id'], unique=False)

    # Create user_sessions table
    op.create_table('user_sessions',
        sa.Column('id', sa.Integer(), nullable=False, comment='会话ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('session_token', sa.String(length=255), nullable=False, comment='会话令牌'),
        sa.Column('ip_address', sa.String(length=45), nullable=True, comment='IP地址'),
        sa.Column('user_agent', sa.Text(), nullable=True, comment='用户代理'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否活跃'),
        sa.Column('last_activity', sa.DateTime(), nullable=True, comment='最后活动时间'),
        sa.Column('expires_at', sa.DateTime(), nullable=False, comment='过期时间'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_token'),
        comment='用户会话表，跟踪用户登录会话'
    )
    op.create_index(op.f('ix_user_sessions_id'), 'user_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_user_sessions_session_token'), 'user_sessions', ['session_token'], unique=False)

    # Create user_login_logs table
    op.create_table('user_login_logs',
        sa.Column('id', sa.Integer(), nullable=False, comment='日志ID'),
        sa.Column('user_id', sa.Integer(), nullable=True, comment='用户ID'),
        sa.Column('email', sa.String(length=255), nullable=False, comment='登录邮箱'),
        sa.Column('ip_address', sa.String(length=45), nullable=True, comment='IP地址'),
        sa.Column('user_agent', sa.Text(), nullable=True, comment='用户代理'),
        sa.Column('login_method', sa.String(length=50), nullable=False, comment='登录方式'),
        sa.Column('is_successful', sa.Boolean(), nullable=False, comment='是否成功'),
        sa.Column('failure_reason', sa.String(length=200), nullable=True, comment='失败原因'),
        sa.Column('session_id', sa.String(length=255), nullable=True, comment='会话ID'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='登录时间'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='用户登录日志表，记录用户登录历史'
    )
    op.create_index(op.f('ix_user_login_logs_id'), 'user_login_logs', ['id'], unique=False)
    op.create_index(op.f('ix_user_login_logs_created_at'), 'user_login_logs', ['created_at'], unique=False)

    # Create user_security_settings table
    op.create_table('user_security_settings',
        sa.Column('id', sa.Integer(), nullable=False, comment='设置ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('two_factor_enabled', sa.Boolean(), nullable=True, comment='是否启用双因子认证'),
        sa.Column('two_factor_secret', sa.String(length=255), nullable=True, comment='双因子认证密钥'),
        sa.Column('backup_codes', sa.Text(), nullable=True, comment='备用验证码'),
        sa.Column('password_changed_at', sa.DateTime(), nullable=True, comment='密码最后修改时间'),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=True, comment='失败登录尝试次数'),
        sa.Column('account_locked_until', sa.DateTime(), nullable=True, comment='账户锁定到期时间'),
        sa.Column('last_password_reset', sa.DateTime(), nullable=True, comment='最后密码重置时间'),
        sa.Column('security_questions', sa.Text(), nullable=True, comment='安全问题'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
        comment='用户安全设置表，存储用户的安全相关设置'
    )
    op.create_index(op.f('ix_user_security_settings_id'), 'user_security_settings', ['id'], unique=False)

    # Create role_permissions association table
    op.create_table('role_permissions',
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('role_id', 'permission_id'),
        comment='角色权限关联表'
    )

    # Create user_roles association table
    op.create_table('user_roles',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'role_id'),
        comment='用户角色关联表'
    )

    # Create user_group_members association table
    op.create_table('user_group_members',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['user_groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'group_id'),
        comment='用户组成员关联表'
    )

    # Create group_roles association table
    op.create_table('group_roles',
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['user_groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('group_id', 'role_id'),
        comment='用户组角色关联表'
    )


def downgrade():
    # Drop association tables first
    op.drop_table('group_roles')
    op.drop_table('user_group_members')
    op.drop_table('user_roles')
    op.drop_table('role_permissions')
    
    # Drop main tables
    op.drop_index(op.f('ix_user_security_settings_id'), table_name='user_security_settings')
    op.drop_table('user_security_settings')
    
    op.drop_index(op.f('ix_user_login_logs_created_at'), table_name='user_login_logs')
    op.drop_index(op.f('ix_user_login_logs_id'), table_name='user_login_logs')
    op.drop_table('user_login_logs')
    
    op.drop_index(op.f('ix_user_sessions_session_token'), table_name='user_sessions')
    op.drop_index(op.f('ix_user_sessions_id'), table_name='user_sessions')
    op.drop_table('user_sessions')
    
    op.drop_index(op.f('ix_user_groups_id'), table_name='user_groups')
    op.drop_table('user_groups')
    
    op.drop_index(op.f('ix_roles_id'), table_name='roles')
    op.drop_table('roles')
    
    op.drop_index(op.f('ix_permissions_id'), table_name='permissions')
    op.drop_table('permissions')
