"""
性能监控和重试机制日志记录模块
"""
from typing import Dict, Any
from .base_logger import BaseLogger


class PerformanceLogger(BaseLogger):
    """性能监控和重试机制日志记录器"""

    @classmethod
    def rag_performance_metrics(
        cls,
        operation: str,
        duration: float,
        memory_usage: int = 0,
        cpu_usage: float = 0.0,
        kb_id: int = None,
        **kwargs,
    ):
        """记录RAG性能指标日志

        Args:
            operation: 操作类型
            duration: 执行耗时(秒)
            memory_usage: 内存使用量(字节)
            cpu_usage: CPU使用率(百分比)
            kb_id: 知识库ID
            **kwargs: 额外的日志字段
        """
        kb_info = f" - 知识库ID: {kb_id}" if kb_id else ""
        memory_info = f" - 内存: {memory_usage / 1024 / 1024:.1f}MB" if memory_usage > 0 else ""
        cpu_info = f" - CPU: {cpu_usage:.1f}%" if cpu_usage > 0 else ""
        
        cls.debug(
            f"RAG性能指标: {operation} - 耗时: {duration:.3f}秒{memory_info}{cpu_info}{kb_info}",
            rag_operation_type="performance_metrics",
            operation=operation,
            duration=duration,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            kb_id=kb_id,
            **kwargs
        )

    @classmethod
    def rag_retry_attempt(
        cls, operation: str, attempt: int, max_retries: int, **kwargs
    ):
        """记录RAG重试尝试日志

        Args:
            operation: 操作名称
            attempt: 当前尝试次数
            max_retries: 最大重试次数
            **kwargs: 额外的日志字段
        """
        cls.warning(
            f"RAG重试尝试: {operation} - 第 {attempt}/{max_retries} 次尝试",
            rag_operation_type="retry_attempt",
            operation=operation,
            attempt_number=attempt,
            max_retries=max_retries,
            **kwargs
        )

    @classmethod
    def rag_retry_success(cls, operation: str, final_attempt: int, **kwargs):
        """记录RAG重试成功日志

        Args:
            operation: 操作名称
            final_attempt: 最终成功的尝试次数
            **kwargs: 额外的日志字段
        """
        cls.info(
            f"RAG重试成功: {operation} - 第 {final_attempt} 次尝试成功",
            rag_operation_type="retry_success",
            operation=operation,
            final_attempt=final_attempt,
            **kwargs
        )

    @classmethod
    def rag_retry_failed(cls, operation: str, attempt: int, error: str, **kwargs):
        """记录RAG重试失败日志

        Args:
            operation: 操作名称
            attempt: 尝试次数
            error: 错误信息
            **kwargs: 额外的日志字段
        """
        cls.warning(
            f"RAG重试失败: {operation} - 第 {attempt} 次尝试失败 - 错误: {error}",
            rag_operation_type="retry_failed",
            operation=operation,
            attempt_number=attempt,
            error_message=error,
            **kwargs
        )

    @classmethod
    def rag_retry_exhausted(
        cls, operation: str, total_attempts: int, final_error: str, **kwargs
    ):
        """记录RAG重试耗尽日志

        Args:
            operation: 操作名称
            total_attempts: 总尝试次数
            final_error: 最终错误信息
            **kwargs: 额外的日志字段
        """
        cls.error(
            f"RAG重试耗尽: {operation} - 总共尝试 {total_attempts} 次均失败 - 最终错误: {final_error}",
            rag_operation_type="retry_exhausted",
            operation=operation,
            total_attempts=total_attempts,
            final_error=final_error,
            **kwargs
        )

    @classmethod
    def rag_cache_operation(
        cls,
        operation: str,
        cache_key: str,
        hit: bool = None,
        data_size: int = 0,
        duration: float = 0.0,
        **kwargs,
    ):
        """记录RAG缓存操作日志

        Args:
            operation: 缓存操作类型 (get, set, delete, clear)
            cache_key: 缓存键
            hit: 是否命中（仅对get操作有效）
            data_size: 数据大小
            duration: 操作耗时(秒)
            **kwargs: 额外的日志字段
        """
        hit_info = ""
        if operation == "get" and hit is not None:
            hit_info = f" - {'命中' if hit else '未命中'}"

        size_info = f" - 数据大小: {data_size}" if data_size > 0 else ""

        cls.debug(
            f"RAG缓存操作: {operation} - 键: {cache_key}{hit_info}{size_info} - 耗时: {duration:.3f}秒",
            rag_operation_type="cache_operation",
            cache_operation=operation,
            cache_key=cache_key,
            cache_hit=hit,
            data_size=data_size,
            operation_duration=duration,
            **kwargs,
        )

    @classmethod
    def rag_model_load(
        cls,
        model_type: str,
        model_name: str,
        success: bool,
        duration: float = 0.0,
        model_size: int = 0,
        **kwargs,
    ):
        """记录RAG模型加载日志

        Args:
            model_type: 模型类型 (embedding, rerank, llm)
            model_name: 模型名称
            success: 是否成功
            duration: 加载耗时(秒)
            model_size: 模型大小
            **kwargs: 额外的日志字段
        """
        status = "成功" if success else "失败"
        level = cls.info if success else cls.error
        size_info = f" - 模型大小: {model_size}" if model_size > 0 else ""

        level(
            f"RAG模型加载{status}: 类型: {model_type} - 名称: {model_name} - 耗时: {duration:.2f}秒{size_info}",
            rag_operation_type="model_load",
            model_type=model_type,
            model_name=model_name,
            load_success=success,
            load_duration=duration,
            model_size=model_size,
            **kwargs,
        )

    @classmethod
    def rag_batch_operation(
        cls,
        operation: str,
        batch_size: int,
        total_items: int,
        current_batch: int,
        total_batches: int,
        **kwargs,
    ):
        """记录RAG批处理操作日志

        Args:
            operation: 操作类型
            batch_size: 批处理大小
            total_items: 总项目数
            current_batch: 当前批次
            total_batches: 总批次数
            **kwargs: 额外的日志字段
        """
        progress = (current_batch / total_batches * 100) if total_batches > 0 else 0

        cls.debug(
            f"RAG批处理: {operation} - 批次 {current_batch}/{total_batches} - 批大小: {batch_size} - 进度: {progress:.1f}%",
            rag_operation_type="batch_operation",
            operation=operation,
            batch_size=batch_size,
            total_items=total_items,
            current_batch=current_batch,
            total_batches=total_batches,
            progress_percent=progress,
            **kwargs,
        )
