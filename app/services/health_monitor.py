import asyncio
import aiohttp
import psutil
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload

from app.models.health import (
    ServiceHealth, SystemAlert, PerformanceThreshold, 
    HealthCheckConfig, UptimeRecord, HealthStatus, AlertLevel
)
from app.models.database import AsyncSessionLocal
from app.schemas.health import (
    ServiceHealthResponse, SystemHealthOverview, SystemAlertResponse,
    SystemResourceMetrics, HealthDashboardData, SystemAlertCreate
)
from app.core.logger import Logger
from app.core.redis_manager import redis_manager
from app.core.config import settings

class HealthMonitorService:
    """健康监控服务
    
    提供系统健康检查、警告管理、性能监控等功能
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def get_system_health_overview(self) -> SystemHealthOverview:
        """获取系统健康概览"""
        try:
            # 获取最近的服务健康状态
            recent_time = datetime.now() - timedelta(minutes=10)
            
            # 查询最近的健康检查结果
            query = select(
                ServiceHealth.status,
                func.count(ServiceHealth.id).label('count')
            ).where(
                ServiceHealth.timestamp >= recent_time
            ).group_by(ServiceHealth.status)
            
            result = await self.db.execute(query)
            status_counts = {row.status: row.count for row in result.fetchall()}
            
            healthy_services = status_counts.get(HealthStatus.HEALTHY, 0)
            warning_services = status_counts.get(HealthStatus.WARNING, 0)
            critical_services = status_counts.get(HealthStatus.CRITICAL, 0)
            total_services = sum(status_counts.values())
            
            # 确定整体状态
            if critical_services > 0:
                overall_status = HealthStatus.CRITICAL
            elif warning_services > 0:
                overall_status = HealthStatus.WARNING
            elif healthy_services > 0:
                overall_status = HealthStatus.HEALTHY
            else:
                overall_status = HealthStatus.UNKNOWN
            
            # 获取系统运行时间
            system_uptime = await self._get_system_uptime()
            
            # 获取最后检查时间
            last_check_result = await self.db.execute(
                select(func.max(ServiceHealth.timestamp))
            )
            last_check = last_check_result.scalar() or datetime.now()
            
            return SystemHealthOverview(
                overall_status=overall_status,
                healthy_services=healthy_services,
                warning_services=warning_services,
                critical_services=critical_services,
                total_services=total_services,
                system_uptime=system_uptime,
                last_check=last_check
            )
            
        except Exception as e:
            Logger.error(f"获取系统健康概览失败: {str(e)}")
            raise
    
    async def get_service_health_status(
        self,
        service_name: Optional[str] = None,
        limit: int = 50
    ) -> List[ServiceHealthResponse]:
        """获取服务健康状态"""
        try:
            # 构建查询
            query = select(ServiceHealth).order_by(desc(ServiceHealth.timestamp))
            
            if service_name:
                query = query.where(ServiceHealth.service_name == service_name)
            
            query = query.limit(limit)
            
            result = await self.db.execute(query)
            health_records = result.scalars().all()
            
            # 转换为响应模型
            services = []
            for record in health_records:
                # 获取运行时间百分比
                uptime_percentage = await self._get_service_uptime(record.service_name)
                
                services.append(ServiceHealthResponse(
                    service_name=record.service_name,
                    service_type=record.service_type,
                    status=record.status,
                    response_time=record.response_time,
                    error_message=record.error_message,
                    details=record.details,
                    timestamp=record.timestamp,
                    uptime_percentage=uptime_percentage
                ))
            
            return services
            
        except Exception as e:
            Logger.error(f"获取服务健康状态失败: {str(e)}")
            raise
    
    async def perform_health_check(self, service_name: str) -> ServiceHealthResponse:
        """执行单个服务的健康检查"""
        try:
            # 获取健康检查配置
            config_result = await self.db.execute(
                select(HealthCheckConfig).where(
                    and_(
                        HealthCheckConfig.service_name == service_name,
                        HealthCheckConfig.is_enabled == True
                    )
                )
            )
            config = config_result.scalar_one_or_none()
            
            if not config:
                raise ValueError(f"未找到服务 {service_name} 的健康检查配置")
            
            # 执行健康检查
            start_time = time.time()
            status = HealthStatus.UNKNOWN
            error_message = None
            details = {}
            
            try:
                if config.check_url:
                    # HTTP健康检查
                    status, error_message, details = await self._check_http_health(
                        config.check_url, config.timeout, config.expected_response
                    )
                elif config.check_command:
                    # 命令行健康检查
                    status, error_message, details = await self._check_command_health(
                        config.check_command, config.timeout
                    )
                else:
                    # 默认检查（基于服务类型）
                    status, error_message, details = await self._check_default_health(
                        config.service_type, config.config_data
                    )
                    
            except Exception as e:
                status = HealthStatus.CRITICAL
                error_message = str(e)
                Logger.error(f"健康检查执行失败: {service_name} - {str(e)}")
            
            response_time = (time.time() - start_time) * 1000  # 转换为毫秒
            
            # 保存健康检查结果
            health_record = ServiceHealth(
                service_name=service_name,
                service_type=config.service_type,
                status=status,
                response_time=response_time,
                error_message=error_message,
                details=details
            )
            
            self.db.add(health_record)
            await self.db.commit()
            
            # 检查是否需要生成警告
            await self._check_and_create_alerts(health_record)
            
            # 获取运行时间百分比
            uptime_percentage = await self._get_service_uptime(service_name)
            
            return ServiceHealthResponse(
                service_name=service_name,
                service_type=config.service_type,
                status=status,
                response_time=response_time,
                error_message=error_message,
                details=details,
                timestamp=health_record.timestamp,
                uptime_percentage=uptime_percentage
            )
            
        except Exception as e:
            Logger.error(f"执行健康检查失败: {service_name} - {str(e)}")
            raise
    
    async def get_system_resource_metrics(self) -> SystemResourceMetrics:
        """获取系统资源指标"""
        try:
            # 获取CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 获取内存信息
            memory = psutil.virtual_memory()
            
            # 获取磁盘信息
            disk = psutil.disk_usage('/')
            
            # 获取网络信息
            network = psutil.net_io_counters()
            
            # 获取系统负载
            load_average = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
            
            return SystemResourceMetrics(
                cpu_usage=cpu_percent,
                memory_usage=memory.percent,
                memory_total=memory.total,
                memory_used=memory.used,
                disk_usage=disk.percent,
                disk_total=disk.total,
                disk_used=disk.used,
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv,
                load_average=load_average,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            Logger.error(f"获取系统资源指标失败: {str(e)}")
            raise
    
    async def create_alert(self, alert_data: SystemAlertCreate) -> SystemAlertResponse:
        """创建系统警告"""
        try:
            alert = SystemAlert(
                alert_type=alert_data.alert_type,
                level=alert_data.level,
                title=alert_data.title,
                message=alert_data.message,
                source=alert_data.source,
                alert_metadata=alert_data.metadata
            )
            
            self.db.add(alert)
            await self.db.commit()
            await self.db.refresh(alert)
            
            # 发送通知
            await self._send_alert_notification(alert)
            
            return SystemAlertResponse(
                id=alert.id,
                alert_type=alert.alert_type,
                level=alert.level,
                title=alert.title,
                message=alert.message,
                source=alert.source,
                metadata=alert.alert_metadata,
                is_resolved=alert.is_resolved,
                resolved_at=alert.resolved_at,
                resolved_by=alert.resolved_by,
                created_at=alert.created_at
            )
            
        except Exception as e:
            Logger.error(f"创建系统警告失败: {str(e)}")
            raise
    
    async def _check_http_health(
        self, 
        url: str, 
        timeout: int, 
        expected_response: Optional[str] = None
    ) -> Tuple[str, Optional[str], Dict[str, Any]]:
        """HTTP健康检查"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.get(url) as response:
                    status_code = response.status
                    response_text = await response.text()
                    
                    details = {
                        "status_code": status_code,
                        "response_size": len(response_text),
                        "headers": dict(response.headers)
                    }
                    
                    if status_code == 200:
                        if expected_response and expected_response not in response_text:
                            return HealthStatus.WARNING, f"响应内容不匹配期望值", details
                        return HealthStatus.HEALTHY, None, details
                    elif status_code < 500:
                        return HealthStatus.WARNING, f"HTTP状态码: {status_code}", details
                    else:
                        return HealthStatus.CRITICAL, f"HTTP状态码: {status_code}", details
                        
        except asyncio.TimeoutError:
            return HealthStatus.CRITICAL, "请求超时", {"timeout": timeout}
        except Exception as e:
            return HealthStatus.CRITICAL, str(e), {"error_type": type(e).__name__}
    
    async def _check_command_health(
        self, 
        command: str, 
        timeout: int
    ) -> Tuple[str, Optional[str], Dict[str, Any]]:
        """命令行健康检查"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=timeout
            )
            
            details = {
                "return_code": process.returncode,
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else ""
            }
            
            if process.returncode == 0:
                return HealthStatus.HEALTHY, None, details
            else:
                return HealthStatus.CRITICAL, f"命令执行失败，返回码: {process.returncode}", details
                
        except asyncio.TimeoutError:
            return HealthStatus.CRITICAL, "命令执行超时", {"timeout": timeout}
        except Exception as e:
            return HealthStatus.CRITICAL, str(e), {"error_type": type(e).__name__}
    
    async def _check_default_health(
        self, 
        service_type: str, 
        config_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Optional[str], Dict[str, Any]]:
        """默认健康检查（基于服务类型）"""
        try:
            if service_type == "database":
                return await self._check_database_health()
            elif service_type == "redis":
                return await self._check_redis_health()
            elif service_type == "system":
                return await self._check_system_health()
            else:
                return HealthStatus.UNKNOWN, f"未知服务类型: {service_type}", {}
                
        except Exception as e:
            return HealthStatus.CRITICAL, str(e), {"error_type": type(e).__name__}
    
    async def _check_database_health(self) -> Tuple[str, Optional[str], Dict[str, Any]]:
        """数据库健康检查"""
        try:
            # 执行简单查询测试数据库连接
            result = await self.db.execute(select(func.count()).select_from(ServiceHealth))
            count = result.scalar()
            
            details = {"record_count": count}
            return HealthStatus.HEALTHY, None, details
            
        except Exception as e:
            return HealthStatus.CRITICAL, f"数据库连接失败: {str(e)}", {}
    
    async def _check_redis_health(self) -> Tuple[str, Optional[str], Dict[str, Any]]:
        """Redis健康检查"""
        try:
            # 测试Redis连接
            await redis_manager.set("health_check", "ok", expire=60)
            result = await redis_manager.get("health_check")
            
            if result == "ok":
                details = {"connection": "ok"}
                return HealthStatus.HEALTHY, None, details
            else:
                return HealthStatus.WARNING, "Redis响应异常", {"response": result}
                
        except Exception as e:
            return HealthStatus.CRITICAL, f"Redis连接失败: {str(e)}", {}
    
    async def _check_system_health(self) -> Tuple[str, Optional[str], Dict[str, Any]]:
        """系统健康检查"""
        try:
            # 检查系统资源使用情况
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            details = {
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "disk_usage": disk.percent
            }
            
            # 根据资源使用情况判断健康状态
            if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
                return HealthStatus.CRITICAL, "系统资源使用率过高", details
            elif cpu_percent > 80 or memory.percent > 80 or disk.percent > 80:
                return HealthStatus.WARNING, "系统资源使用率较高", details
            else:
                return HealthStatus.HEALTHY, None, details
                
        except Exception as e:
            return HealthStatus.CRITICAL, f"系统检查失败: {str(e)}", {}
    
    async def _get_system_uptime(self) -> float:
        """获取系统运行时间"""
        try:
            # 尝试从Redis获取启动时间
            start_time_str = await redis_manager.get("system:start_time")
            if start_time_str:
                start_time = datetime.fromisoformat(start_time_str)
                uptime_seconds = (datetime.now() - start_time).total_seconds()
                return uptime_seconds / 3600  # 转换为小时
            else:
                # 使用系统启动时间
                boot_time = datetime.fromtimestamp(psutil.boot_time())
                uptime_seconds = (datetime.now() - boot_time).total_seconds()
                return uptime_seconds / 3600
        except Exception:
            return 0.0
    
    async def _get_service_uptime(self, service_name: str) -> Optional[float]:
        """获取服务运行时间百分比"""
        try:
            # 获取最近24小时的健康检查记录
            start_time = datetime.now() - timedelta(hours=24)
            
            result = await self.db.execute(
                select(
                    func.count(ServiceHealth.id).label('total'),
                    func.sum(
                        func.case(
                            (ServiceHealth.status == HealthStatus.HEALTHY, 1),
                            else_=0
                        )
                    ).label('healthy')
                ).where(
                    and_(
                        ServiceHealth.service_name == service_name,
                        ServiceHealth.timestamp >= start_time
                    )
                )
            )
            
            row = result.first()
            if row and row.total > 0:
                return (row.healthy / row.total) * 100
            return None
            
        except Exception:
            return None
    
    async def _check_and_create_alerts(self, health_record: ServiceHealth):
        """检查并创建警告"""
        try:
            if health_record.status in [HealthStatus.WARNING, HealthStatus.CRITICAL]:
                # 检查是否已有未解决的相同警告
                existing_alert = await self.db.execute(
                    select(SystemAlert).where(
                        and_(
                            SystemAlert.alert_type == "service_health",
                            SystemAlert.source == health_record.service_name,
                            SystemAlert.is_resolved == False
                        )
                    )
                )
                
                if not existing_alert.scalar_one_or_none():
                    # 创建新警告
                    alert_level = AlertLevel.CRITICAL if health_record.status == HealthStatus.CRITICAL else AlertLevel.WARNING
                    
                    alert = SystemAlert(
                        alert_type="service_health",
                        level=alert_level,
                        title=f"服务健康异常: {health_record.service_name}",
                        message=health_record.error_message or f"服务状态: {health_record.status}",
                        source=health_record.service_name,
                        alert_metadata={
                            "service_type": health_record.service_type,
                            "response_time": health_record.response_time,
                            "details": health_record.details
                        }
                    )
                    
                    self.db.add(alert)
                    await self.db.commit()
                    
                    # 发送通知
                    await self._send_alert_notification(alert)
                    
        except Exception as e:
            Logger.error(f"检查和创建警告失败: {str(e)}")
    
    async def _send_alert_notification(self, alert: SystemAlert):
        """发送警告通知"""
        try:
            # 这里可以实现各种通知方式：邮件、Slack、钉钉等
            Logger.warning(f"系统警告: {alert.title} - {alert.message}")
            
            # 存储到Redis用于实时通知
            alert_data = {
                "id": alert.id,
                "type": alert.alert_type,
                "level": alert.level,
                "title": alert.title,
                "message": alert.message,
                "timestamp": alert.created_at.isoformat()
            }
            
            await redis_manager.lpush(
                "system_alerts:realtime",
                str(alert_data),
                expire=3600  # 1小时过期
            )
            
        except Exception as e:
            Logger.error(f"发送警告通知失败: {str(e)}")

class HealthCheckScheduler:
    """健康检查调度器

    定期执行健康检查任务
    """

    def __init__(self):
        self.running = False
        self.tasks = {}

    async def start(self):
        """启动健康检查调度器"""
        self.running = True

        # 获取所有启用的健康检查配置
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(HealthCheckConfig).where(HealthCheckConfig.is_enabled == True)
            )
            configs = result.scalars().all()

            # 为每个配置创建定时任务
            for config in configs:
                task = asyncio.create_task(
                    self._schedule_health_check(config)
                )
                self.tasks[config.service_name] = task

        Logger.info(f"健康检查调度器已启动，共 {len(self.tasks)} 个检查任务")

    async def stop(self):
        """停止健康检查调度器"""
        self.running = False

        # 取消所有任务
        for task in self.tasks.values():
            task.cancel()

        # 等待所有任务完成
        if self.tasks:
            await asyncio.gather(*self.tasks.values(), return_exceptions=True)

        self.tasks.clear()
        Logger.info("健康检查调度器已停止")

    async def _schedule_health_check(self, config: HealthCheckConfig):
        """调度单个健康检查"""
        while self.running:
            try:
                async with AsyncSessionLocal() as db:
                    health_service = HealthMonitorService(db)
                    await health_service.perform_health_check(config.service_name)

                # 等待下次检查
                await asyncio.sleep(config.check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                Logger.error(f"健康检查调度异常: {config.service_name} - {str(e)}")
                await asyncio.sleep(config.check_interval)

# 全局健康检查调度器实例
health_scheduler = HealthCheckScheduler()
