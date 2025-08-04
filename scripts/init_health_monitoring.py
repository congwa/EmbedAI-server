#!/usr/bin/env python3
"""
初始化健康监控配置脚本

该脚本创建默认的健康检查配置和性能阈值设置
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.database import AsyncSessionLocal
from app.models.health import HealthCheckConfig, PerformanceThreshold
from app.core.logger import Logger

async def create_default_health_checks():
    """创建默认健康检查配置"""
    
    default_configs = [
        {
            "service_name": "database",
            "service_type": "database",
            "check_interval": 60,
            "timeout": 15,
            "retry_count": 3,
            "is_enabled": True
        },
        {
            "service_name": "redis",
            "service_type": "redis",
            "check_interval": 60,
            "timeout": 10,
            "retry_count": 3,
            "is_enabled": True
        },
        {
            "service_name": "system",
            "service_type": "system",
            "check_interval": 120,
            "timeout": 30,
            "retry_count": 1,
            "is_enabled": True
        },
        {
            "service_name": "api_server",
            "service_type": "api",
            "check_interval": 300,
            "timeout": 30,
            "retry_count": 2,
            "is_enabled": True,
            "check_url": "http://localhost:8000/health",
            "expected_response": "OK"
        }
    ]
    
    async with AsyncSessionLocal() as db:
        try:
            for config_data in default_configs:
                # 检查是否已存在
                from sqlalchemy import select
                result = await db.execute(
                    select(HealthCheckConfig).where(
                        HealthCheckConfig.service_name == config_data["service_name"]
                    )
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    config = HealthCheckConfig(**config_data)
                    db.add(config)
                    Logger.info(f"创建健康检查配置: {config_data['service_name']}")
                else:
                    Logger.info(f"健康检查配置已存在: {config_data['service_name']}")
            
            await db.commit()
            Logger.info("默认健康检查配置创建完成")
            
        except Exception as e:
            await db.rollback()
            Logger.error(f"创建健康检查配置失败: {str(e)}")
            raise

async def create_default_thresholds():
    """创建默认性能阈值"""
    
    default_thresholds = [
        {
            "metric_name": "cpu_usage",
            "metric_type": "system",
            "warning_threshold": 80.0,
            "critical_threshold": 95.0,
            "comparison_operator": "gt",
            "unit": "%",
            "description": "CPU使用率阈值",
            "is_enabled": True
        },
        {
            "metric_name": "memory_usage",
            "metric_type": "system",
            "warning_threshold": 85.0,
            "critical_threshold": 95.0,
            "comparison_operator": "gt",
            "unit": "%",
            "description": "内存使用率阈值",
            "is_enabled": True
        },
        {
            "metric_name": "disk_usage",
            "metric_type": "system",
            "warning_threshold": 80.0,
            "critical_threshold": 90.0,
            "comparison_operator": "gt",
            "unit": "%",
            "description": "磁盘使用率阈值",
            "is_enabled": True
        },
        {
            "metric_name": "response_time",
            "metric_type": "api",
            "warning_threshold": 2000.0,
            "critical_threshold": 5000.0,
            "comparison_operator": "gt",
            "unit": "ms",
            "description": "API响应时间阈值",
            "is_enabled": True
        },
        {
            "metric_name": "error_rate",
            "metric_type": "api",
            "warning_threshold": 5.0,
            "critical_threshold": 10.0,
            "comparison_operator": "gt",
            "unit": "%",
            "description": "API错误率阈值",
            "is_enabled": True
        },
        {
            "metric_name": "load_average",
            "metric_type": "system",
            "warning_threshold": 2.0,
            "critical_threshold": 4.0,
            "comparison_operator": "gt",
            "unit": "",
            "description": "系统负载阈值",
            "is_enabled": True
        }
    ]
    
    async with AsyncSessionLocal() as db:
        try:
            for threshold_data in default_thresholds:
                # 检查是否已存在
                from sqlalchemy import select
                result = await db.execute(
                    select(PerformanceThreshold).where(
                        PerformanceThreshold.metric_name == threshold_data["metric_name"]
                    )
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    threshold = PerformanceThreshold(**threshold_data)
                    db.add(threshold)
                    Logger.info(f"创建性能阈值: {threshold_data['metric_name']}")
                else:
                    Logger.info(f"性能阈值已存在: {threshold_data['metric_name']}")
            
            await db.commit()
            Logger.info("默认性能阈值创建完成")
            
        except Exception as e:
            await db.rollback()
            Logger.error(f"创建性能阈值失败: {str(e)}")
            raise

async def init_redis_startup_time():
    """在Redis中设置系统启动时间"""
    try:
        from app.core.redis_manager import redis_manager
        from datetime import datetime
        
        # 设置系统启动时间
        start_time = datetime.now().isoformat()
        await redis_manager.set("system:start_time", start_time)
        Logger.info(f"系统启动时间已设置: {start_time}")
        
    except Exception as e:
        Logger.error(f"设置系统启动时间失败: {str(e)}")

async def main():
    """主函数"""
    try:
        Logger.info("开始初始化健康监控配置...")
        
        # 创建默认健康检查配置
        await create_default_health_checks()
        
        # 创建默认性能阈值
        await create_default_thresholds()
        
        # 初始化Redis启动时间
        await init_redis_startup_time()
        
        Logger.info("健康监控配置初始化完成!")
        
    except Exception as e:
        Logger.error(f"初始化失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
