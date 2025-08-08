"""性能监控中间件

监控API响应时间、内存使用情况和请求处理性能
"""

import time
import psutil
import asyncio
from typing import Callable, Dict, Any, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.logger import Logger
from app.core.response import ResponseModel


class PerformanceMetrics:
    """性能指标收集器"""
    
    def __init__(self):
        """初始化性能指标收集器"""
        self.request_count = 0
        self.total_response_time = 0.0
        self.slow_requests = []
        self.error_count = 0
        self.memory_usage_samples = []
        self.endpoint_stats = {}
    
    def record_request(
        self, 
        method: str, 
        path: str, 
        response_time: float, 
        status_code: int,
        memory_usage: float
    ) -> None:
        """记录请求性能数据
        
        Args:
            method: HTTP方法
            path: 请求路径
            response_time: 响应时间（秒）
            status_code: HTTP状态码
            memory_usage: 内存使用量（MB）
        """
        self.request_count += 1
        self.total_response_time += response_time
        
        # 记录慢请求（超过1秒）
        if response_time > 1.0:
            self.slow_requests.append({
                "method": method,
                "path": path,
                "response_time": response_time,
                "timestamp": time.time(),
                "memory_usage": memory_usage
            })
            
            # 只保留最近100个慢请求
            if len(self.slow_requests) > 100:
                self.slow_requests.pop(0)
        
        # 记录错误请求
        if status_code >= 400:
            self.error_count += 1
        
        # 记录内存使用情况
        self.memory_usage_samples.append(memory_usage)
        if len(self.memory_usage_samples) > 1000:
            self.memory_usage_samples.pop(0)
        
        # 记录端点统计
        endpoint_key = f"{method} {path}"
        if endpoint_key not in self.endpoint_stats:
            self.endpoint_stats[endpoint_key] = {
                "count": 0,
                "total_time": 0.0,
                "min_time": float('inf'),
                "max_time": 0.0,
                "error_count": 0
            }
        
        stats = self.endpoint_stats[endpoint_key]
        stats["count"] += 1
        stats["total_time"] += response_time
        stats["min_time"] = min(stats["min_time"], response_time)
        stats["max_time"] = max(stats["max_time"], response_time)
        
        if status_code >= 400:
            stats["error_count"] += 1
    
    def get_average_response_time(self) -> float:
        """获取平均响应时间"""
        if self.request_count == 0:
            return 0.0
        return self.total_response_time / self.request_count
    
    def get_error_rate(self) -> float:
        """获取错误率"""
        if self.request_count == 0:
            return 0.0
        return (self.error_count / self.request_count) * 100
    
    def get_average_memory_usage(self) -> float:
        """获取平均内存使用量"""
        if not self.memory_usage_samples:
            return 0.0
        return sum(self.memory_usage_samples) / len(self.memory_usage_samples)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要
        
        Returns:
            Dict[str, Any]: 性能摘要数据
        """
        return {
            "total_requests": self.request_count,
            "average_response_time": round(self.get_average_response_time(), 4),
            "error_rate": round(self.get_error_rate(), 2),
            "slow_requests_count": len(self.slow_requests),
            "average_memory_usage": round(self.get_average_memory_usage(), 2),
            "top_slow_endpoints": self._get_top_slow_endpoints(),
            "top_error_endpoints": self._get_top_error_endpoints()
        }
    
    def _get_top_slow_endpoints(self, limit: int = 5) -> list:
        """获取最慢的端点"""
        sorted_endpoints = sorted(
            self.endpoint_stats.items(),
            key=lambda x: x[1]["total_time"] / x[1]["count"],
            reverse=True
        )
        
        return [
            {
                "endpoint": endpoint,
                "average_time": round(stats["total_time"] / stats["count"], 4),
                "request_count": stats["count"]
            }
            for endpoint, stats in sorted_endpoints[:limit]
        ]
    
    def _get_top_error_endpoints(self, limit: int = 5) -> list:
        """获取错误最多的端点"""
        sorted_endpoints = sorted(
            self.endpoint_stats.items(),
            key=lambda x: x[1]["error_count"],
            reverse=True
        )
        
        return [
            {
                "endpoint": endpoint,
                "error_count": stats["error_count"],
                "error_rate": round((stats["error_count"] / stats["count"]) * 100, 2)
            }
            for endpoint, stats in sorted_endpoints[:limit]
            if stats["error_count"] > 0
        ]


# 全局性能指标收集器
performance_metrics = PerformanceMetrics()


class PerformanceMiddleware(BaseHTTPMiddleware):
    """性能监控中间件"""
    
    def __init__(
        self, 
        app,
        slow_request_threshold: float = 1.0,
        memory_warning_threshold: float = 500.0,
        enable_detailed_logging: bool = True
    ):
        """初始化性能监控中间件
        
        Args:
            app: FastAPI应用实例
            slow_request_threshold: 慢请求阈值（秒）
            memory_warning_threshold: 内存警告阈值（MB）
            enable_detailed_logging: 是否启用详细日志
        """
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
        self.memory_warning_threshold = memory_warning_threshold
        self.enable_detailed_logging = enable_detailed_logging
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并监控性能
        
        Args:
            request: HTTP请求
            call_next: 下一个中间件或路由处理器
            
        Returns:
            Response: HTTP响应
        """
        # 记录开始时间和内存使用
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        # 获取请求信息
        method = request.method
        path = self._get_clean_path(request.url.path)
        
        try:
            # 执行请求处理
            response = await call_next(request)
            
            # 计算性能指标
            end_time = time.time()
            end_memory = self._get_memory_usage()
            response_time = end_time - start_time
            memory_delta = end_memory - start_memory
            
            # 记录性能数据
            performance_metrics.record_request(
                method=method,
                path=path,
                response_time=response_time,
                status_code=response.status_code,
                memory_usage=end_memory
            )
            
            # 添加性能头信息
            response.headers["X-Response-Time"] = f"{response_time:.4f}s"
            response.headers["X-Memory-Usage"] = f"{end_memory:.2f}MB"
            
            # 记录性能日志
            await self._log_performance(
                method, path, response_time, response.status_code, 
                end_memory, memory_delta
            )
            
            # 检查性能警告
            await self._check_performance_warnings(
                method, path, response_time, end_memory, response.status_code
            )
            
            return response
            
        except Exception as e:
            # 处理异常情况
            end_time = time.time()
            end_memory = self._get_memory_usage()
            response_time = end_time - start_time
            
            # 记录异常性能数据
            performance_metrics.record_request(
                method=method,
                path=path,
                response_time=response_time,
                status_code=500,
                memory_usage=end_memory
            )
            
            Logger.error(
                f"请求处理异常: {method} {path}",
                response_time=response_time,
                memory_usage=end_memory,
                error=str(e)
            )
            
            # 重新抛出异常，让全局异常处理器处理
            raise
    
    def _get_memory_usage(self) -> float:
        """获取当前内存使用量（MB）
        
        Returns:
            float: 内存使用量（MB）
        """
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            return memory_info.rss / 1024 / 1024  # 转换为MB
        except Exception:
            return 0.0
    
    def _get_clean_path(self, path: str) -> str:
        """清理路径，移除动态参数
        
        Args:
            path: 原始路径
            
        Returns:
            str: 清理后的路径
        """
        # 简单的路径参数替换，将数字ID替换为{id}
        import re
        # 替换数字ID
        path = re.sub(r'/\d+', '/{id}', path)
        # 替换UUID
        path = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '/{uuid}', path)
        return path
    
    async def _log_performance(
        self, 
        method: str, 
        path: str, 
        response_time: float, 
        status_code: int,
        memory_usage: float,
        memory_delta: float
    ) -> None:
        """记录性能日志
        
        Args:
            method: HTTP方法
            path: 请求路径
            response_time: 响应时间
            status_code: HTTP状态码
            memory_usage: 内存使用量
            memory_delta: 内存变化量
        """
        if self.enable_detailed_logging:
            Logger.info(
                f"请求性能: {method} {path}",
                response_time=f"{response_time:.4f}s",
                status_code=status_code,
                memory_usage=f"{memory_usage:.2f}MB",
                memory_delta=f"{memory_delta:+.2f}MB"
            )
    
    async def _check_performance_warnings(
        self, 
        method: str, 
        path: str, 
        response_time: float, 
        memory_usage: float,
        status_code: int
    ) -> None:
        """检查性能警告
        
        Args:
            method: HTTP方法
            path: 请求路径
            response_time: 响应时间
            memory_usage: 内存使用量
            status_code: HTTP状态码
        """
        warnings = []
        
        # 检查慢请求
        if response_time > self.slow_request_threshold:
            warnings.append(f"慢请求警告: 响应时间 {response_time:.4f}s 超过阈值 {self.slow_request_threshold}s")
        
        # 检查内存使用
        if memory_usage > self.memory_warning_threshold:
            warnings.append(f"内存警告: 内存使用 {memory_usage:.2f}MB 超过阈值 {self.memory_warning_threshold}MB")
        
        # 检查错误状态码
        if status_code >= 500:
            warnings.append(f"服务器错误: HTTP状态码 {status_code}")
        elif status_code >= 400:
            warnings.append(f"客户端错误: HTTP状态码 {status_code}")
        
        # 记录警告
        if warnings:
            Logger.warning(
                f"性能警告: {method} {path}",
                warnings=warnings,
                response_time=response_time,
                memory_usage=memory_usage,
                status_code=status_code
            )


async def get_performance_stats() -> Dict[str, Any]:
    """获取性能统计信息
    
    Returns:
        Dict[str, Any]: 性能统计数据
    """
    return performance_metrics.get_performance_summary()


async def reset_performance_stats() -> None:
    """重置性能统计信息"""
    global performance_metrics
    performance_metrics = PerformanceMetrics()
    Logger.info("性能统计信息已重置")


# 性能监控API端点（可选）
def create_performance_endpoints():
    """创建性能监控API端点"""
    from fastapi import APIRouter
    
    router = APIRouter(prefix="/performance", tags=["performance"])
    
    @router.get("/stats", response_model=ResponseModel[Dict[str, Any]])
    async def get_performance_statistics():
        """获取性能统计信息"""
        stats = await get_performance_stats()
        return ResponseModel.create_success(
            data=stats,
            message="获取性能统计成功"
        )
    
    @router.post("/reset", response_model=ResponseModel[Dict[str, Any]])
    async def reset_performance_statistics():
        """重置性能统计信息"""
        await reset_performance_stats()
        return ResponseModel.create_success(
            data={"reset": True},
            message="性能统计重置成功"
        )
    
    return router