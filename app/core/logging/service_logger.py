"""
服务调用相关日志记录模块
"""
from typing import Dict, Any
from .base_logger import BaseLogger


class ServiceLogger(BaseLogger):
    """服务调用相关日志记录器"""

    @classmethod
    def service_call(cls, service: str, method: str, **kwargs):
        """记录服务调用日志

        Args:
            service: 服务名称
            method: 方法名称
            **kwargs: 额外的日志字段
        """
        cls.debug(
            f"服务调用: {service}.{method}",
            service_name=service,
            service_method=method,
            **kwargs
        )

    @classmethod
    def service_result(
        cls, service: str, method: str, success: bool, process_time: float, **kwargs
    ):
        """记录服务调用结果日志

        Args:
            service: 服务名称
            method: 方法名称
            success: 是否成功
            process_time: 处理时间(秒)
            **kwargs: 额外的日志字段
        """
        status = "成功" if success else "失败"
        level = cls.debug if success else cls.error
        
        level(
            f"服务调用{status}: {service}.{method} - 耗时: {process_time:.3f}秒",
            service_name=service,
            service_method=method,
            service_success=success,
            service_process_time=process_time,
            **kwargs
        )
