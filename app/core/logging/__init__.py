"""
日志记录模块

提供统一的日志记录接口，支持：
1. 链路追踪 - 通过trace_id关联同一请求的所有日志
2. 详细中文日志 - 提供丰富的上下文信息
3. 结构化日志 - 支持JSON格式输出
4. 多级日志 - 支持不同级别的日志记录
5. 性能记录 - 支持记录操作耗时
6. RAG特定日志 - 支持RAG相关的专门日志记录

使用方式:
    from app.core.logging import Logger
    
    # 初始化追踪
    trace_id = Logger.init_trace()
    
    # 记录基础日志
    Logger.info("这是一条信息日志")
    Logger.error("这是一条错误日志")
    
    # 记录API日志
    Logger.api_request("POST", "/api/chat", {"message": "hello"})
    Logger.api_response("POST", "/api/chat", 200, 0.5)
    
    # 记录RAG日志
    Logger.rag_query_start(kb_id=1, query="什么是AI？")
    Logger.rag_query_complete(kb_id=1, query="什么是AI？", success=True, duration=1.2, result_count=5)
"""

from .trace_context import RAGTraceContext, trace_context
from .base_logger import BaseLogger
from .api_logger import APILogger
from .database_logger import DatabaseLogger
from .service_logger import ServiceLogger
from .rag_logger import RAGLogger
from .performance_logger import PerformanceLogger
from .operation_logger import OperationLogger


class Logger(BaseLogger):
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


__all__ = [
    'Logger',
    'RAGTraceContext',
    'trace_context',
    'BaseLogger',
    'APILogger',
    'DatabaseLogger',
    'ServiceLogger',
    'RAGLogger',
    'PerformanceLogger',
    'OperationLogger',
]
