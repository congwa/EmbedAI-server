"""向后兼容的日志模块入口

为了保持向后兼容性，这个文件现在导入新的模块化日志系统。
原有的使用方式 `from app.core.logger import Logger` 保持不变。

这个文件本身不包含任何日志记录的实现，
它只是一个指向 `app.core.logging` 中统一日志记录器的门面。
"""

# 导入并重新导出新的模块化日志系统中的所有组件
from .logging import (
    Logger,
    RAGTraceContext,
    trace_context,
    BaseLogger,
    APILogger,
    DatabaseLogger,
    ServiceLogger,
    RAGLogger,
    PerformanceLogger,
)

# 通过 __all__ 明确暴露公共 API，确保向后兼容性
__all__ = [
    'Logger',  # 统一的日志记录器
    'RAGTraceContext',  # RAG 链路追踪上下文
    'trace_context',  # 全局链路追踪上下文实例
    'BaseLogger',
    'APILogger',
    'DatabaseLogger',
    'ServiceLogger',
    'RAGLogger',
    'PerformanceLogger',
]
