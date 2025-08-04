"""Add configuration management tables

Revision ID: 005
Revises: 004
Create Date: 2024-08-04 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    # Create system_configs table
    op.create_table('system_configs',
        sa.Column('id', sa.Integer(), nullable=False, comment='配置ID'),
        sa.Column('key', sa.String(length=100), nullable=False, comment='配置键名'),
        sa.Column('value', sa.Text(), nullable=True, comment='配置值'),
        sa.Column('default_value', sa.Text(), nullable=True, comment='默认值'),
        sa.Column('description', sa.Text(), nullable=True, comment='配置描述'),
        sa.Column('category', sa.Enum('SYSTEM', 'DATABASE', 'REDIS', 'EMAIL', 'STORAGE', 'AI_MODEL', 'SECURITY', 'LOGGING', 'MONITORING', 'INTEGRATION', name='configcategory'), nullable=False, comment='配置分类'),
        sa.Column('type', sa.Enum('STRING', 'INTEGER', 'FLOAT', 'BOOLEAN', 'JSON', 'PASSWORD', 'EMAIL', 'URL', 'FILE_PATH', name='configtype'), nullable=False, comment='配置类型'),
        sa.Column('is_sensitive', sa.Boolean(), nullable=True, comment='是否为敏感信息'),
        sa.Column('is_required', sa.Boolean(), nullable=True, comment='是否必需'),
        sa.Column('is_readonly', sa.Boolean(), nullable=True, comment='是否只读'),
        sa.Column('is_system', sa.Boolean(), nullable=True, comment='是否为系统配置'),
        sa.Column('validation_rule', sa.Text(), nullable=True, comment='验证规则（正则表达式或JSON）'),
        sa.Column('options', sa.JSON(), nullable=True, comment='可选值列表（用于枚举类型）'),
        sa.Column('min_value', sa.String(length=50), nullable=True, comment='最小值'),
        sa.Column('max_value', sa.String(length=50), nullable=True, comment='最大值'),
        sa.Column('restart_required', sa.Boolean(), nullable=True, comment='修改后是否需要重启'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key'),
        comment='系统配置表，存储系统的各种配置参数'
    )
    op.create_index(op.f('ix_system_configs_id'), 'system_configs', ['id'], unique=False)
    op.create_index(op.f('ix_system_configs_key'), 'system_configs', ['key'], unique=False)

    # Create config_change_logs table
    op.create_table('config_change_logs',
        sa.Column('id', sa.Integer(), nullable=False, comment='日志ID'),
        sa.Column('config_id', sa.Integer(), nullable=False, comment='配置ID'),
        sa.Column('config_key', sa.String(length=100), nullable=False, comment='配置键名'),
        sa.Column('old_value', sa.Text(), nullable=True, comment='旧值'),
        sa.Column('new_value', sa.Text(), nullable=True, comment='新值'),
        sa.Column('change_type', sa.String(length=20), nullable=False, comment='变更类型'),
        sa.Column('user_id', sa.Integer(), nullable=True, comment='操作用户ID'),
        sa.Column('user_email', sa.String(length=255), nullable=True, comment='操作用户邮箱'),
        sa.Column('ip_address', sa.String(length=45), nullable=True, comment='操作IP地址'),
        sa.Column('user_agent', sa.Text(), nullable=True, comment='用户代理'),
        sa.Column('reason', sa.Text(), nullable=True, comment='变更原因'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='变更时间'),
        sa.ForeignKeyConstraint(['config_id'], ['system_configs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='配置变更日志表，记录配置的变更历史'
    )
    op.create_index(op.f('ix_config_change_logs_id'), 'config_change_logs', ['id'], unique=False)
    op.create_index(op.f('ix_config_change_logs_created_at'), 'config_change_logs', ['created_at'], unique=False)

    # Create config_templates table
    op.create_table('config_templates',
        sa.Column('id', sa.Integer(), nullable=False, comment='模板ID'),
        sa.Column('name', sa.String(length=100), nullable=False, comment='模板名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='模板描述'),
        sa.Column('category', sa.Enum('SYSTEM', 'DATABASE', 'REDIS', 'EMAIL', 'STORAGE', 'AI_MODEL', 'SECURITY', 'LOGGING', 'MONITORING', 'INTEGRATION', name='configcategory'), nullable=False, comment='模板分类'),
        sa.Column('template_data', sa.JSON(), nullable=False, comment='模板配置数据'),
        sa.Column('is_system', sa.Boolean(), nullable=True, comment='是否为系统模板'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否激活'),
        sa.Column('version', sa.String(length=20), nullable=False, comment='模板版本'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        comment='配置模板表，预定义的配置模板'
    )
    op.create_index(op.f('ix_config_templates_id'), 'config_templates', ['id'], unique=False)

    # Create config_backups table
    op.create_table('config_backups',
        sa.Column('id', sa.Integer(), nullable=False, comment='备份ID'),
        sa.Column('name', sa.String(length=100), nullable=False, comment='备份名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='备份描述'),
        sa.Column('backup_data', sa.JSON(), nullable=False, comment='备份的配置数据'),
        sa.Column('config_count', sa.Integer(), nullable=False, comment='配置项数量'),
        sa.Column('backup_type', sa.String(length=20), nullable=False, comment='备份类型'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='备份时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='备份人ID'),
        sa.Column('created_by_email', sa.String(length=255), nullable=True, comment='备份人邮箱'),
        sa.PrimaryKeyConstraint('id'),
        comment='配置备份表，系统配置的备份记录'
    )
    op.create_index(op.f('ix_config_backups_id'), 'config_backups', ['id'], unique=False)
    op.create_index(op.f('ix_config_backups_created_at'), 'config_backups', ['created_at'], unique=False)

    # Create environment_variables table
    op.create_table('environment_variables',
        sa.Column('id', sa.Integer(), nullable=False, comment='变量ID'),
        sa.Column('name', sa.String(length=100), nullable=False, comment='变量名'),
        sa.Column('value', sa.Text(), nullable=True, comment='变量值'),
        sa.Column('description', sa.Text(), nullable=True, comment='变量描述'),
        sa.Column('category', sa.Enum('SYSTEM', 'DATABASE', 'REDIS', 'EMAIL', 'STORAGE', 'AI_MODEL', 'SECURITY', 'LOGGING', 'MONITORING', 'INTEGRATION', name='configcategory'), nullable=False, comment='变量分类'),
        sa.Column('is_sensitive', sa.Boolean(), nullable=True, comment='是否为敏感信息'),
        sa.Column('is_required', sa.Boolean(), nullable=True, comment='是否必需'),
        sa.Column('is_system', sa.Boolean(), nullable=True, comment='是否为系统变量'),
        sa.Column('validation_rule', sa.Text(), nullable=True, comment='验证规则'),
        sa.Column('default_value', sa.Text(), nullable=True, comment='默认值'),
        sa.Column('restart_required', sa.Boolean(), nullable=True, comment='修改后是否需要重启'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        comment='环境变量表，管理系统环境变量'
    )
    op.create_index(op.f('ix_environment_variables_id'), 'environment_variables', ['id'], unique=False)
    op.create_index(op.f('ix_environment_variables_name'), 'environment_variables', ['name'], unique=False)

    # Create config_validation_rules table
    op.create_table('config_validation_rules',
        sa.Column('id', sa.Integer(), nullable=False, comment='规则ID'),
        sa.Column('name', sa.String(length=100), nullable=False, comment='规则名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='规则描述'),
        sa.Column('rule_type', sa.String(length=50), nullable=False, comment='规则类型'),
        sa.Column('rule_data', sa.JSON(), nullable=False, comment='规则数据'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误消息模板'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否激活'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        comment='配置验证规则表，定义配置项的验证规则'
    )
    op.create_index(op.f('ix_config_validation_rules_id'), 'config_validation_rules', ['id'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_config_validation_rules_id'), table_name='config_validation_rules')
    op.drop_table('config_validation_rules')
    
    op.drop_index(op.f('ix_environment_variables_name'), table_name='environment_variables')
    op.drop_index(op.f('ix_environment_variables_id'), table_name='environment_variables')
    op.drop_table('environment_variables')
    
    op.drop_index(op.f('ix_config_backups_created_at'), table_name='config_backups')
    op.drop_index(op.f('ix_config_backups_id'), table_name='config_backups')
    op.drop_table('config_backups')
    
    op.drop_index(op.f('ix_config_templates_id'), table_name='config_templates')
    op.drop_table('config_templates')
    
    op.drop_index(op.f('ix_config_change_logs_created_at'), table_name='config_change_logs')
    op.drop_index(op.f('ix_config_change_logs_id'), table_name='config_change_logs')
    op.drop_table('config_change_logs')
    
    op.drop_index(op.f('ix_system_configs_key'), table_name='system_configs')
    op.drop_index(op.f('ix_system_configs_id'), table_name='system_configs')
    op.drop_table('system_configs')
