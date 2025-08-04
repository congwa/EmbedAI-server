import time
import psutil
import asyncio
from datetime import datetime
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logger import Logger
from app.models.database import AsyncSessionLocal
from app.services.analytics import AnalyticsService
from app.models.analytics import APIMetrics, SystemMetrics
from app.core.redis_manager import redis_manager

class AnalyticsMiddleware(BaseHTTPMiddleware):
    """分析中间件
    
    自动收集API调用指标、系统性能数据和用户活动信息
    """
    
    def __init__(self, app, collect_system_metrics: bool = True):
        super().__init__(app)
        self.collect_system_metrics = collect_system_metrics
        self.last_system_metrics_time = 0
        self.system_metrics_interval = 60  # 每60秒收集一次系统指标
        
    async def dispatch(self, request: Request, call_next):
        """处理请求并收集分析数据"""
        start_time = time.time()
        
        # 提取请求信息
        endpoint = request.url.path
        method = request.method
        ip_address = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # 获取用户ID(如果已认证)
        user_id = await self._extract_user_id(request)
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算响应时间
            response_time = time.time() - start_time
            
            # 异步记录API指标
            asyncio.create_task(self._record_api_metrics(
                endpoint=endpoint,
                method=method,
                status_code=response.status_code,
                response_time=response_time,
                user_id=user_id,
                ip_address=ip_address
            ))
            
            # 记录用户活动(如果是认证用户)
            if user_id:
                asyncio.create_task(self._record_user_activity(
                    user_id=user_id,
                    activity_type="api_call",
                    details={
                        "endpoint": endpoint,
                        "method": method,
                        "status_code": response.status_code,
                        "response_time": response_time
                    },
                    ip_address=ip_address,
                    user_agent=user_agent
                ))
            
            # 定期收集系统指标
            if self.collect_system_metrics:
                current_time = time.time()
                if current_time - self.last_system_metrics_time > self.system_metrics_interval:
                    asyncio.create_task(self._collect_system_metrics())
                    self.last_system_metrics_time = current_time
            
            return response
            
        except Exception as e:
            # 记录错误指标
            response_time = time.time() - start_time
            asyncio.create_task(self._record_api_metrics(
                endpoint=endpoint,
                method=method,
                status_code=500,
                response_time=response_time,
                user_id=user_id,
                ip_address=ip_address
            ))
            
            Logger.error(f"请求处理异常: {endpoint} - {str(e)}")
            raise
    
    async def _record_api_metrics(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time: float,
        user_id: Optional[int],
        ip_address: str
    ):
        """记录API指标"""
        try:
            async with AsyncSessionLocal() as db:
                api_metric = APIMetrics(
                    endpoint=endpoint,
                    method=method,
                    status_code=status_code,
                    response_time=response_time,
                    user_id=user_id,
                    ip_address=ip_address
                )
                
                db.add(api_metric)
                await db.commit()
                
                # 同时存储到Redis用于实时监控
                metric_data = {
                    "endpoint": endpoint,
                    "method": method,
                    "status_code": status_code,
                    "response_time": response_time,
                    "timestamp": datetime.now().isoformat()
                }
                
                await redis_manager.lpush(
                    "api_metrics:realtime",
                    str(metric_data),
                    expire=3600  # 1小时过期
                )
                
        except Exception as e:
            Logger.error(f"记录API指标失败: {str(e)}")
    
    async def _record_user_activity(
        self,
        user_id: int,
        activity_type: str,
        details: dict,
        ip_address: str,
        user_agent: str
    ):
        """记录用户活动"""
        try:
            async with AsyncSessionLocal() as db:
                analytics_service = AnalyticsService(db)
                await analytics_service.record_user_activity(
                    user_id=user_id,
                    activity_type=activity_type,
                    details=details,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
        except Exception as e:
            Logger.error(f"记录用户活动失败: {str(e)}")
    
    async def _collect_system_metrics(self):
        """收集系统性能指标"""
        try:
            # 获取系统指标
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # 获取网络统计
            network = psutil.net_io_counters()
            
            metrics = {
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "memory_total": memory.total,
                "memory_used": memory.used,
                "disk_usage": disk.percent,
                "disk_total": disk.total,
                "disk_used": disk.used,
                "network_bytes_sent": network.bytes_sent,
                "network_bytes_recv": network.bytes_recv
            }
            
            # 存储到数据库
            async with AsyncSessionLocal() as db:
                analytics_service = AnalyticsService(db)
                await analytics_service.record_system_metrics(metrics)
            
            # 存储到Redis用于实时监控
            await redis_manager.hset(
                "system_metrics:current",
                mapping={k: str(v) for k, v in metrics.items()}
            )
            await redis_manager.expire("system_metrics:current", 300)  # 5分钟过期
            
        except Exception as e:
            Logger.error(f"收集系统指标失败: {str(e)}")
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 检查代理头
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 返回直接连接的IP
        return request.client.host if request.client else "unknown"
    
    async def _extract_user_id(self, request: Request) -> Optional[int]:
        """从请求中提取用户ID"""
        try:
            # 尝试从Authorization头获取token并解析用户ID
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None
            
            token = auth_header.split(" ")[1]
            
            # 这里需要解析JWT token获取用户ID
            # 为了避免循环导入，我们简化处理
            # 实际实现中应该使用JWT解析
            
            # 暂时从Redis缓存中获取用户ID
            user_id_str = await redis_manager.get(f"token:{token}")
            if user_id_str:
                return int(user_id_str)
            
            return None
            
        except Exception:
            return None

class SystemMetricsCollector:
    """系统指标收集器
    
    独立的后台任务，定期收集系统指标
    """
    
    def __init__(self, interval: int = 60):
        self.interval = interval
        self.running = False
    
    async def start(self):
        """启动指标收集"""
        self.running = True
        while self.running:
            try:
                await self._collect_metrics()
                await asyncio.sleep(self.interval)
            except Exception as e:
                Logger.error(f"系统指标收集异常: {str(e)}")
                await asyncio.sleep(self.interval)
    
    async def stop(self):
        """停止指标收集"""
        self.running = False
    
    async def _collect_metrics(self):
        """收集指标"""
        try:
            # 获取系统指标
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # 获取进程信息
            process = psutil.Process()
            process_memory = process.memory_info()
            
            metrics = {
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "disk_usage": disk.percent,
                "process_memory": process_memory.rss,
                "load_average": psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
            }
            
            # 存储到数据库
            async with AsyncSessionLocal() as db:
                analytics_service = AnalyticsService(db)
                await analytics_service.record_system_metrics(metrics)
            
            Logger.debug(f"系统指标收集完成: CPU={cpu_percent}%, Memory={memory.percent}%")
            
        except Exception as e:
            Logger.error(f"收集系统指标失败: {str(e)}")

# 全局指标收集器实例
metrics_collector = SystemMetricsCollector()
