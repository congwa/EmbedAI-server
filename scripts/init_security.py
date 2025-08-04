#!/usr/bin/env python3
"""
初始化安全系统脚本

该脚本创建默认的安全策略和配置
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.database import AsyncSessionLocal
from app.models.security import SecurityPolicy, SecurityEvent, SecurityEventType
from app.core.logger import Logger

async def create_default_security_policies():
    """创建默认安全策略"""
    
    default_policies = [
        {
            "name": "密码复杂度策略",
            "description": "定义密码复杂度要求",
            "policy_type": "password_policy",
            "rules": {
                "min_length": 8,
                "max_length": 128,
                "require_uppercase": True,
                "require_lowercase": True,
                "require_numbers": True,
                "require_symbols": False,
                "forbidden_patterns": ["123456", "password", "admin"],
                "history_check": 5
            },
            "is_active": True,
            "priority": 100
        },
        {
            "name": "登录安全策略",
            "description": "定义登录安全规则",
            "policy_type": "login_policy",
            "rules": {
                "max_failed_attempts": 5,
                "lockout_duration": 1800,  # 30分钟
                "session_timeout": 3600,   # 1小时
                "require_2fa_for_admin": True,
                "allow_concurrent_sessions": 3,
                "ip_whitelist_enabled": False,
                "suspicious_activity_threshold": 10
            },
            "is_active": True,
            "priority": 90
        },
        {
            "name": "IP访问控制策略",
            "description": "定义IP访问控制规则",
            "policy_type": "ip_access_policy",
            "rules": {
                "whitelist_mode": False,
                "auto_block_enabled": True,
                "auto_block_threshold": 10,
                "auto_block_duration": 3600,  # 1小时
                "trusted_ip_ranges": [],
                "blocked_countries": [],
                "rate_limit_per_ip": 100
            },
            "is_active": True,
            "priority": 80
        },
        {
            "name": "会话管理策略",
            "description": "定义会话管理规则",
            "policy_type": "session_policy",
            "rules": {
                "max_session_duration": 86400,  # 24小时
                "idle_timeout": 3600,           # 1小时
                "require_reauth_for_sensitive": True,
                "device_fingerprinting": True,
                "trusted_device_duration": 2592000,  # 30天
                "force_logout_on_password_change": True
            },
            "is_active": True,
            "priority": 70
        },
        {
            "name": "双因子认证策略",
            "description": "定义双因子认证规则",
            "policy_type": "two_factor_policy",
            "rules": {
                "mandatory_for_admin": True,
                "mandatory_for_sensitive_operations": False,
                "allowed_methods": ["totp", "sms", "email"],
                "backup_codes_count": 10,
                "grace_period": 7,  # 7天宽限期
                "remember_device_duration": 2592000  # 30天
            },
            "is_active": True,
            "priority": 85
        },
        {
            "name": "数据保护策略",
            "description": "定义数据保护规则",
            "policy_type": "data_protection_policy",
            "rules": {
                "encrypt_sensitive_data": True,
                "mask_sensitive_logs": True,
                "data_retention_days": 365,
                "audit_log_retention_days": 2555,  # 7年
                "backup_encryption": True,
                "secure_delete": True
            },
            "is_active": True,
            "priority": 95
        },
        {
            "name": "API安全策略",
            "description": "定义API安全规则",
            "policy_type": "api_security_policy",
            "rules": {
                "rate_limit_per_user": 1000,
                "rate_limit_per_ip": 100,
                "require_https": True,
                "api_key_rotation_days": 90,
                "request_size_limit": 10485760,  # 10MB
                "response_headers_security": True
            },
            "is_active": True,
            "priority": 75
        },
        {
            "name": "审计日志策略",
            "description": "定义审计日志规则",
            "policy_type": "audit_policy",
            "rules": {
                "log_all_admin_actions": True,
                "log_failed_authentications": True,
                "log_privilege_escalations": True,
                "log_data_access": True,
                "log_configuration_changes": True,
                "real_time_alerting": True,
                "alert_thresholds": {
                    "failed_logins": 5,
                    "privilege_escalations": 1,
                    "suspicious_activities": 3
                }
            },
            "is_active": True,
            "priority": 90
        }
    ]
    
    async with AsyncSessionLocal() as db:
        try:
            for policy_data in default_policies:
                # 检查是否已存在
                from sqlalchemy import select
                result = await db.execute(
                    select(SecurityPolicy).where(SecurityPolicy.name == policy_data["name"])
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    policy = SecurityPolicy(**policy_data)
                    db.add(policy)
                    Logger.info(f"创建安全策略: {policy_data['name']}")
                else:
                    Logger.info(f"安全策略已存在: {policy_data['name']}")
            
            await db.commit()
            Logger.info("默认安全策略创建完成")
            
        except Exception as e:
            await db.rollback()
            Logger.error(f"创建默认安全策略失败: {str(e)}")
            raise

async def create_initial_security_events():
    """创建初始安全事件（用于演示）"""
    
    initial_events = [
        {
            "event_type": SecurityEventType.LOGIN_SUCCESS.value,
            "severity": "info",
            "ip_address": "127.0.0.1",
            "user_agent": "Mozilla/5.0 (System Initialization)",
            "details": {
                "message": "系统初始化完成",
                "component": "security_system"
            },
            "risk_score": 0
        },
        {
            "event_type": SecurityEventType.SUSPICIOUS_ACTIVITY.value,
            "severity": "warning",
            "ip_address": "192.168.1.100",
            "details": {
                "message": "检测到可疑活动模式",
                "pattern": "multiple_failed_logins",
                "threshold_exceeded": True
            },
            "risk_score": 60
        }
    ]
    
    async with AsyncSessionLocal() as db:
        try:
            for event_data in initial_events:
                event = SecurityEvent(**event_data)
                db.add(event)
                Logger.info(f"创建安全事件: {event_data['event_type']}")
            
            await db.commit()
            Logger.info("初始安全事件创建完成")
            
        except Exception as e:
            await db.rollback()
            Logger.error(f"创建初始安全事件失败: {str(e)}")
            raise

async def setup_security_configurations():
    """设置安全配置"""
    
    try:
        # 这里可以添加其他安全配置的初始化
        # 比如创建默认的IP白名单、黑名单等
        
        Logger.info("安全配置设置完成")
        
    except Exception as e:
        Logger.error(f"设置安全配置失败: {str(e)}")
        raise

async def main():
    """主函数"""
    try:
        Logger.info("开始初始化安全系统...")
        
        # 创建默认安全策略
        await create_default_security_policies()
        
        # 创建初始安全事件
        await create_initial_security_events()
        
        # 设置安全配置
        await setup_security_configurations()
        
        Logger.info("安全系统初始化完成!")
        Logger.info("安全功能包括:")
        Logger.info("- 双因子认证 (2FA)")
        Logger.info("- 增强会话管理")
        Logger.info("- IP访问控制")
        Logger.info("- 安全事件监控")
        Logger.info("- 密码安全策略")
        Logger.info("- 设备指纹识别")
        Logger.info("- 安全审计日志")
        Logger.info("- 安全策略管理")
        
    except Exception as e:
        Logger.error(f"安全系统初始化失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
