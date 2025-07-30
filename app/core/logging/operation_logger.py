"""
通用操作日志记录器模块
"""
import time
import uuid
from typing import Optional, Dict, Any

from .base_logger import BaseLogger


class OperationLogger(BaseLogger):
    """
    通用操作日志记录器，提供开始、成功、失败的统一日志记录模式。
    """

    _operation_starts: Dict[str, float] = {}

    @classmethod
    def _get_operation_key(cls, operation_id: str, operation_type: str) -> str:
        """生成操作的唯一键"""
        trace_id = cls.get_trace_id() or 'main'
        return f"{trace_id}:{operation_type}:{operation_id}"

    @classmethod
    def operation_start(
        cls,
        operation_type: str,
        operation_id: Optional[str] = None,
        message: str = "",
        **kwargs
    ) -> str:
        """
        记录一个操作的开始。

        Args:
            operation_type (str): 操作的类型 (e.g., 'database_query', 'file_processing').
            operation_id (str, optional): 操作的唯一标识符. 如果不提供则自动生成.
            message (str, optional): 自定义日志消息. Defaults to "".
            **kwargs: 附加的日志上下文.
        
        Returns:
            str: 本次操作的唯一ID
        """
        op_id = operation_id or str(uuid.uuid4())
        key = cls._get_operation_key(op_id, operation_type)
        cls._operation_starts[key] = time.time()

        log_message = message or f"开始操作: {operation_type}"
        cls.info(
            log_message,
            operation_status="start",
            operation_type=operation_type,
            operation_id=op_id,
            **kwargs
        )
        return op_id

    @classmethod
    def operation_success(
        cls,
        operation_type: str,
        operation_id: str,
        message: str = "",
        **kwargs
    ):
        """
        记录一个操作的成功完成。

        Args:
            operation_type (str): 操作的类型。
            operation_id (str): 操作的唯一标识符 (由 operation_start 返回)。
            message (str, optional): 自定义日志消息. Defaults to "".
            **kwargs: 附加的日志上下文.
        """
        key = cls._get_operation_key(operation_id, operation_type)
        start_time = cls._operation_starts.pop(key, None)
        duration = (time.time() - start_time) if start_time else -1

        log_message = message or f"操作成功: {operation_type}"
        cls.info(
            f"{log_message} - 耗时: {duration:.3f}秒",
            operation_status="success",
            operation_type=operation_type,
            operation_id=operation_id,
            duration=duration,
            **kwargs
        )

    @classmethod
    def operation_error(
        cls,
        operation_type: str,
        operation_id: str,
        error: Any,
        message: str = "",
        **kwargs
    ):
        """
        记录一个操作的失败。

        Args:
            operation_type (str): 操作的类型。
            operation_id (str): 操作的唯一标识符 (由 operation_start 返回)。
            error (Any): 发生的错误或异常。
            message (str, optional): 自定义日志消息. Defaults to "".
            **kwargs: 附加的日志上下文.
        """
        key = cls._get_operation_key(operation_id, operation_type)
        start_time = cls._operation_starts.pop(key, None)
        duration = (time.time() - start_time) if start_time else -1

        log_message = message or f"操作失败: {operation_type}"
        cls.error(
            f"{log_message} - 错误: {error} - 耗时: {duration:.3f}秒",
            operation_status="error",
            operation_type=operation_type,
            operation_id=operation_id,
            error_message=str(error),
            duration=duration,
            **kwargs
        )
