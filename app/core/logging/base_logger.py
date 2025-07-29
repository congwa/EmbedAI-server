"""
基础日志记录器模块
"""
import logging
import sys
import uuid
import json
import time
import threading
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any, Union

from app.core.config import settings
from .trace_context import trace_context, RAGTraceContext


class BaseLogger:
    """基础日志记录器

    特性:
    1. 链路追踪 - 通过trace_id关联同一请求的所有日志
    2. 详细中文日志 - 提供丰富的上下文信息
    3. 结构化日志 - 支持JSON格式输出
    4. 多级日志 - 支持不同级别的日志记录
    5. 性能记录 - 支持记录操作耗时
    """

    _instance: Optional[logging.Logger] = None

    @classmethod
    def get_logger(cls) -> logging.Logger:
        """获取日志记录器实例"""
        if cls._instance is None:
            cls._instance = cls._setup_logger()
        return cls._instance

    @staticmethod
    def _setup_logger() -> logging.Logger:
        """设置日志记录器"""
        # 创建logger
        logger = logging.getLogger("EmbedAi-Server")
        logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
        logger.propagate = False

        # 如果已经有处理器，则不重复添加
        if logger.handlers:
            return logger

        # 创建格式化器 - 普通文本格式
        text_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] [%(trace_id)s] [%(module)s:%(lineno)d] - %(message)s"
        )

        # 创建格式化器 - JSON格式
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    "timestamp": self.formatTime(record),
                    "level": record.levelname,
                    "trace_id": getattr(record, "trace_id", ""),
                    "module": record.module,
                    "line": record.lineno,
                    "message": record.getMessage(),
                }
                # 添加额外字段
                for key, value in record.__dict__.items():
                    if key not in ["name", "msg", "args", "levelname", "levelno", "pathname", "filename", "module", "lineno", "funcName", "created", "msecs", "relativeCreated", "thread", "threadName", "processName", "process", "getMessage", "exc_info", "exc_text", "stack_info"]:
                        log_entry[key] = value
                return json.dumps(log_entry, ensure_ascii=False)

        # 创建控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
        console_handler.setFormatter(text_formatter)
        logger.addHandler(console_handler)

        # 创建文件处理器
        if hasattr(settings, 'LOG_FILE') and settings.LOG_FILE:
            log_file = Path(settings.LOG_FILE)
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = RotatingFileHandler(
                log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(JsonFormatter())
            logger.addHandler(file_handler)

        return logger

    @staticmethod
    def _get_trace_context() -> Dict[str, Any]:
        """获取当前请求的追踪上下文"""
        try:
            context = trace_context.get()
            if not context:
                return {}
            
            # 如果存在RAG追踪上下文，优先使用
            rag_context = context.get("rag_context")
            if rag_context and isinstance(rag_context, RAGTraceContext):
                return {
                    "trace_id": rag_context.trace_id,
                    "kb_id": rag_context.kb_id,
                    "user_id": rag_context.user_id,
                    "operation_type": rag_context.operation_type,
                }
            
            return context
        except LookupError:
            return {}

    @classmethod
    def init_trace(cls, trace_id: Optional[str] = None, **kwargs) -> str:
        """初始化请求追踪

        Args:
            trace_id: 可选的追踪ID，如果不提供则自动生成
            **kwargs: 其他要添加到追踪上下文的键值对

        Returns:
            str: 追踪ID
        """
        if trace_id is None:
            trace_id = str(uuid.uuid4())
        
        context = {
            "trace_id": trace_id,
            "start_time": time.time(),
            **kwargs
        }
        
        trace_context.set(context)
        
        cls.info(f"开始请求追踪: {trace_id}", trace_id=trace_id, **kwargs)
        return trace_id

    @classmethod
    def init_rag_trace(
        cls,
        kb_id: int,
        user_id: int = None,
        operation_type: str = None,
        trace_id: Optional[str] = None,
    ) -> str:
        """初始化RAG特定的请求追踪

        Args:
            kb_id: 知识库ID
            user_id: 用户ID
            operation_type: 操作类型 ('training', 'query', 'management')
            trace_id: 可选的追踪ID，如果不提供则自动生成

        Returns:
            str: 追踪ID
        """
        if trace_id is None:
            trace_id = str(uuid.uuid4())
        
        rag_context = RAGTraceContext(trace_id)
        rag_context.set_kb_context(kb_id, user_id, operation_type)
        
        context = {
            "trace_id": trace_id,
            "start_time": time.time(),
            "rag_context": rag_context,
            "kb_id": kb_id,
            "user_id": user_id,
            "operation_type": operation_type,
        }
        
        trace_context.set(context)
        
        cls.info(
            f"开始RAG追踪: {trace_id} - 知识库ID: {kb_id} - 操作类型: {operation_type}",
            trace_id=trace_id,
            kb_id=kb_id,
            user_id=user_id,
            operation_type=operation_type,
        )
        return trace_id

    @classmethod
    def get_rag_context(cls) -> Optional[RAGTraceContext]:
        """获取当前的RAG追踪上下文

        Returns:
            Optional[RAGTraceContext]: RAG追踪上下文，如果不存在则返回None
        """
        try:
            context = trace_context.get()
            return context.get("rag_context") if context else None
        except LookupError:
            return None

    @classmethod
    def add_rag_stage(cls, stage_name: str, **kwargs):
        """添加RAG处理阶段

        Args:
            stage_name: 阶段名称
            **kwargs: 阶段相关的额外信息
        """
        rag_context = cls.get_rag_context()
        if rag_context:
            rag_context.add_stage(stage_name, **kwargs)

    @classmethod
    def update_rag_metrics(cls, **metrics):
        """更新RAG性能指标

        Args:
            **metrics: 性能指标键值对
        """
        rag_context = cls.get_rag_context()
        if rag_context:
            rag_context.update_performance_metrics(**metrics)

    @classmethod
    def get_rag_trace_summary(cls) -> Dict[str, Any]:
        """获取RAG追踪摘要信息

        Returns:
            Dict[str, Any]: 追踪摘要信息
        """
        rag_context = cls.get_rag_context()
        if rag_context:
            return rag_context.to_dict()
        return {}

    @classmethod
    def finalize_rag_trace(cls) -> Dict[str, Any]:
        """完成RAG追踪并返回摘要

        Returns:
            Dict[str, Any]: 完整的追踪信息
        """
        rag_context = cls.get_rag_context()
        if rag_context:
            summary = rag_context.to_dict()
            cls.info(
                f"完成RAG追踪: {rag_context.trace_id} - 总耗时: {rag_context.get_total_duration():.2f}秒",
                trace_id=rag_context.trace_id,
                total_duration=rag_context.get_total_duration(),
                stages_count=len(rag_context.stages),
                **summary
            )
            return summary
        return {}

    @classmethod
    def set_rag_operation_context(cls, operation_type: str, **context_data):
        """设置RAG操作上下文信息

        Args:
            operation_type: 操作类型
            **context_data: 上下文数据
        """
        try:
            context = trace_context.get()
            if context:
                context.update({
                    "operation_type": operation_type,
                    **context_data
                })
                trace_context.set(context)
        except LookupError:
            pass

    @classmethod
    def get_trace_id(cls) -> str:
        """获取当前请求的追踪ID"""
        context = cls._get_trace_context()
        return context.get("trace_id", "")

    @classmethod
    def _log(cls, level: int, message: str, extra: Dict[str, Any] = None):
        """记录日志的内部方法

        Args:
            level: 日志级别
            message: 日志消息
            extra: 额外的日志字段
        """
        logger = cls.get_logger()
        
        # 获取追踪上下文
        context = cls._get_trace_context()
        
        # 合并额外字段
        log_extra = {
            "trace_id": context.get("trace_id", ""),
            **(extra or {})
        }
        
        # 记录日志
        logger.log(level, message, extra=log_extra)

    @classmethod
    def info(cls, message: str, **kwargs):
        """记录信息级别日志

        Args:
            message: 日志消息
            **kwargs: 额外的日志字段
        """
        cls._log(logging.INFO, message, kwargs)

    @classmethod
    def error(cls, message: str, **kwargs):
        """记录错误级别日志

        Args:
            message: 日志消息
            **kwargs: 额外的日志字段
        """
        cls._log(logging.ERROR, message, kwargs)

    @classmethod
    def warning(cls, message: str, **kwargs):
        """记录警告级别日志

        Args:
            message: 日志消息
            **kwargs: 额外的日志字段
        """
        cls._log(logging.WARNING, message, kwargs)

    @classmethod
    def debug(cls, message: str, **kwargs):
        """记录调试级别日志

        Args:
            message: 日志消息
            **kwargs: 额外的日志字段
        """
        cls._log(logging.DEBUG, message, kwargs)
