"""
统一的Logger类，整合所有日志功能
"""
from .base_logger import BaseLogger
from .api_logger import APILogger
from .database_logger import DatabaseLogger
from .service_logger import ServiceLogger
from .rag_logger import RAGLogger
from .performance_logger import PerformanceLogger


class Logger(
    BaseLogger,
    APILogger,
    DatabaseLogger,
    ServiceLogger,
    RAGLogger,
    PerformanceLogger
):
    """
    统一的日志记录器类，继承所有功能模块
    
    提供完整的日志记录功能，包括：
    - 基础日志功能 (BaseLogger)
    - API请求/响应日志 (APILogger)
    - 数据库操作日志 (DatabaseLogger)
    - 服务调用日志 (ServiceLogger)
    - RAG特定日志 (RAGLogger)
    - 性能监控日志 (PerformanceLogger)
    """
    pass
