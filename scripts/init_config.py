#!/usr/bin/env python3
"""
初始化系统配置脚本

该脚本创建默认的系统配置、环境变量和配置模板
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.database import AsyncSessionLocal
from app.models.config import SystemConfig, ConfigTemplate, EnvironmentVariable, ConfigType, ConfigCategory
from app.core.logger import Logger

async def create_default_configs():
    """创建默认系统配置"""
    
    default_configs = [
        # 系统配置
        {
            "key": "system_name",
            "value": "EmbedAI Server",
            "default_value": "EmbedAI Server",
            "description": "系统名称",
            "category": ConfigCategory.SYSTEM,
            "type": ConfigType.STRING,
            "is_required": True,
            "is_system": True
        },
        {
            "key": "system_version",
            "value": "1.0.0",
            "default_value": "1.0.0",
            "description": "系统版本",
            "category": ConfigCategory.SYSTEM,
            "type": ConfigType.STRING,
            "is_readonly": True,
            "is_system": True
        },
        {
            "key": "max_upload_size",
            "value": "100",
            "default_value": "100",
            "description": "最大上传文件大小（MB）",
            "category": ConfigCategory.SYSTEM,
            "type": ConfigType.INTEGER,
            "min_value": "1",
            "max_value": "1000",
            "is_required": True
        },
        {
            "key": "session_timeout",
            "value": "3600",
            "default_value": "3600",
            "description": "会话超时时间（秒）",
            "category": ConfigCategory.SECURITY,
            "type": ConfigType.INTEGER,
            "min_value": "300",
            "max_value": "86400",
            "is_required": True
        },
        
        # 数据库配置
        {
            "key": "db_pool_size",
            "value": "10",
            "default_value": "10",
            "description": "数据库连接池大小",
            "category": ConfigCategory.DATABASE,
            "type": ConfigType.INTEGER,
            "min_value": "1",
            "max_value": "100",
            "restart_required": True
        },
        {
            "key": "db_max_overflow",
            "value": "20",
            "default_value": "20",
            "description": "数据库连接池最大溢出",
            "category": ConfigCategory.DATABASE,
            "type": ConfigType.INTEGER,
            "min_value": "0",
            "max_value": "200",
            "restart_required": True
        },
        
        # Redis配置
        {
            "key": "redis_max_connections",
            "value": "50",
            "default_value": "50",
            "description": "Redis最大连接数",
            "category": ConfigCategory.REDIS,
            "type": ConfigType.INTEGER,
            "min_value": "1",
            "max_value": "1000",
            "restart_required": True
        },
        {
            "key": "redis_timeout",
            "value": "5",
            "default_value": "5",
            "description": "Redis连接超时时间（秒）",
            "category": ConfigCategory.REDIS,
            "type": ConfigType.INTEGER,
            "min_value": "1",
            "max_value": "60"
        },
        
        # 邮件配置
        {
            "key": "smtp_host",
            "value": "",
            "default_value": "",
            "description": "SMTP服务器地址",
            "category": ConfigCategory.EMAIL,
            "type": ConfigType.STRING,
            "validation_rule": r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        },
        {
            "key": "smtp_port",
            "value": "587",
            "default_value": "587",
            "description": "SMTP服务器端口",
            "category": ConfigCategory.EMAIL,
            "type": ConfigType.INTEGER,
            "min_value": "1",
            "max_value": "65535"
        },
        {
            "key": "smtp_username",
            "value": "",
            "default_value": "",
            "description": "SMTP用户名",
            "category": ConfigCategory.EMAIL,
            "type": ConfigType.EMAIL
        },
        {
            "key": "smtp_password",
            "value": "",
            "default_value": "",
            "description": "SMTP密码",
            "category": ConfigCategory.EMAIL,
            "type": ConfigType.PASSWORD,
            "is_sensitive": True
        },
        {
            "key": "smtp_use_tls",
            "value": "true",
            "default_value": "true",
            "description": "是否使用TLS加密",
            "category": ConfigCategory.EMAIL,
            "type": ConfigType.BOOLEAN
        },
        
        # AI模型配置
        {
            "key": "openai_api_key",
            "value": "",
            "default_value": "",
            "description": "OpenAI API密钥",
            "category": ConfigCategory.AI_MODEL,
            "type": ConfigType.PASSWORD,
            "is_sensitive": True
        },
        {
            "key": "openai_base_url",
            "value": "https://api.openai.com/v1",
            "default_value": "https://api.openai.com/v1",
            "description": "OpenAI API基础URL",
            "category": ConfigCategory.AI_MODEL,
            "type": ConfigType.URL
        },
        {
            "key": "default_model",
            "value": "gpt-3.5-turbo",
            "default_value": "gpt-3.5-turbo",
            "description": "默认AI模型",
            "category": ConfigCategory.AI_MODEL,
            "type": ConfigType.STRING,
            "options": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "claude-3-sonnet", "claude-3-opus"]
        },
        {
            "key": "max_tokens",
            "value": "4000",
            "default_value": "4000",
            "description": "最大token数量",
            "category": ConfigCategory.AI_MODEL,
            "type": ConfigType.INTEGER,
            "min_value": "100",
            "max_value": "32000"
        },
        {
            "key": "temperature",
            "value": "0.7",
            "default_value": "0.7",
            "description": "模型温度参数",
            "category": ConfigCategory.AI_MODEL,
            "type": ConfigType.FLOAT,
            "min_value": "0.0",
            "max_value": "2.0"
        },
        
        # 安全配置
        {
            "key": "password_min_length",
            "value": "8",
            "default_value": "8",
            "description": "密码最小长度",
            "category": ConfigCategory.SECURITY,
            "type": ConfigType.INTEGER,
            "min_value": "6",
            "max_value": "50"
        },
        {
            "key": "password_require_uppercase",
            "value": "true",
            "default_value": "true",
            "description": "密码是否需要大写字母",
            "category": ConfigCategory.SECURITY,
            "type": ConfigType.BOOLEAN
        },
        {
            "key": "password_require_lowercase",
            "value": "true",
            "default_value": "true",
            "description": "密码是否需要小写字母",
            "category": ConfigCategory.SECURITY,
            "type": ConfigType.BOOLEAN
        },
        {
            "key": "password_require_numbers",
            "value": "true",
            "default_value": "true",
            "description": "密码是否需要数字",
            "category": ConfigCategory.SECURITY,
            "type": ConfigType.BOOLEAN
        },
        {
            "key": "password_require_symbols",
            "value": "false",
            "default_value": "false",
            "description": "密码是否需要特殊字符",
            "category": ConfigCategory.SECURITY,
            "type": ConfigType.BOOLEAN
        },
        {
            "key": "max_login_attempts",
            "value": "5",
            "default_value": "5",
            "description": "最大登录尝试次数",
            "category": ConfigCategory.SECURITY,
            "type": ConfigType.INTEGER,
            "min_value": "3",
            "max_value": "20"
        },
        {
            "key": "account_lockout_duration",
            "value": "1800",
            "default_value": "1800",
            "description": "账户锁定时长（秒）",
            "category": ConfigCategory.SECURITY,
            "type": ConfigType.INTEGER,
            "min_value": "300",
            "max_value": "86400"
        },
        
        # 日志配置
        {
            "key": "log_level",
            "value": "INFO",
            "default_value": "INFO",
            "description": "日志级别",
            "category": ConfigCategory.LOGGING,
            "type": ConfigType.STRING,
            "options": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        },
        {
            "key": "log_max_size",
            "value": "100",
            "default_value": "100",
            "description": "单个日志文件最大大小（MB）",
            "category": ConfigCategory.LOGGING,
            "type": ConfigType.INTEGER,
            "min_value": "1",
            "max_value": "1000"
        },
        {
            "key": "log_backup_count",
            "value": "10",
            "default_value": "10",
            "description": "日志文件备份数量",
            "category": ConfigCategory.LOGGING,
            "type": ConfigType.INTEGER,
            "min_value": "1",
            "max_value": "100"
        },
        
        # 监控配置
        {
            "key": "health_check_interval",
            "value": "60",
            "default_value": "60",
            "description": "健康检查间隔（秒）",
            "category": ConfigCategory.MONITORING,
            "type": ConfigType.INTEGER,
            "min_value": "10",
            "max_value": "3600"
        },
        {
            "key": "metrics_retention_days",
            "value": "30",
            "default_value": "30",
            "description": "指标数据保留天数",
            "category": ConfigCategory.MONITORING,
            "type": ConfigType.INTEGER,
            "min_value": "1",
            "max_value": "365"
        }
    ]
    
    async with AsyncSessionLocal() as db:
        try:
            for config_data in default_configs:
                # 检查是否已存在
                from sqlalchemy import select
                result = await db.execute(
                    select(SystemConfig).where(SystemConfig.key == config_data["key"])
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    config = SystemConfig(**config_data)
                    db.add(config)
                    Logger.info(f"创建配置: {config_data['key']}")
                else:
                    Logger.info(f"配置已存在: {config_data['key']}")
            
            await db.commit()
            Logger.info("默认系统配置创建完成")
            
        except Exception as e:
            await db.rollback()
            Logger.error(f"创建默认系统配置失败: {str(e)}")
            raise

async def create_default_env_vars():
    """创建默认环境变量"""
    
    default_env_vars = [
        {
            "name": "DATABASE_URL",
            "description": "数据库连接URL",
            "category": ConfigCategory.DATABASE,
            "is_sensitive": True,
            "is_required": True,
            "is_system": True,
            "restart_required": True
        },
        {
            "name": "REDIS_URL",
            "description": "Redis连接URL",
            "category": ConfigCategory.REDIS,
            "is_sensitive": True,
            "is_required": True,
            "is_system": True,
            "restart_required": True
        },
        {
            "name": "SECRET_KEY",
            "description": "应用密钥",
            "category": ConfigCategory.SECURITY,
            "is_sensitive": True,
            "is_required": True,
            "is_system": True,
            "restart_required": True
        },
        {
            "name": "JWT_SECRET_KEY",
            "description": "JWT密钥",
            "category": ConfigCategory.SECURITY,
            "is_sensitive": True,
            "is_required": True,
            "is_system": True,
            "restart_required": True
        },
        {
            "name": "ENVIRONMENT",
            "description": "运行环境",
            "category": ConfigCategory.SYSTEM,
            "default_value": "development",
            "validation_rule": r"^(development|staging|production)$",
            "is_required": True,
            "restart_required": True
        }
    ]
    
    async with AsyncSessionLocal() as db:
        try:
            for env_data in default_env_vars:
                # 检查是否已存在
                from sqlalchemy import select
                result = await db.execute(
                    select(EnvironmentVariable).where(EnvironmentVariable.name == env_data["name"])
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    env_var = EnvironmentVariable(**env_data)
                    db.add(env_var)
                    Logger.info(f"创建环境变量: {env_data['name']}")
                else:
                    Logger.info(f"环境变量已存在: {env_data['name']}")
            
            await db.commit()
            Logger.info("默认环境变量创建完成")
            
        except Exception as e:
            await db.rollback()
            Logger.error(f"创建默认环境变量失败: {str(e)}")
            raise

async def main():
    """主函数"""
    try:
        Logger.info("开始初始化系统配置...")
        
        # 创建默认系统配置
        await create_default_configs()
        
        # 创建默认环境变量
        await create_default_env_vars()
        
        Logger.info("系统配置初始化完成!")
        
    except Exception as e:
        Logger.error(f"系统配置初始化失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
