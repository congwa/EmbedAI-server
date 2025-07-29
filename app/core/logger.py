import logging
import sys
import uuid
import json
import time
import threading
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any, Union, List
from contextvars import ContextVar
from app.core.config import settings

# 创建上下文变量，用于存储请求跟踪信息
trace_context: ContextVar[Dict[str, Any]] = ContextVar("trace_context", default={})


class RAGTraceContext:
    """RAG链路追踪上下文管理器"""

    def __init__(self, trace_id: str):
        """初始化RAG追踪上下文

        Args:
            trace_id: 追踪ID
        """
        self.trace_id = trace_id
        self.kb_id: Optional[int] = None
        self.user_id: Optional[int] = None
        self.operation_type: Optional[str] = None  # 'training', 'query', 'management'
        self.start_time: float = time.time()
        self.stages: List[Dict[str, Any]] = []  # 记录各个阶段的信息
        self.performance_metrics: Dict[str, Any] = {}

    def set_kb_context(
        self, kb_id: int, user_id: int = None, operation_type: str = None
    ):
        """设置知识库上下文

        Args:
            kb_id: 知识库ID
            user_id: 用户ID
            operation_type: 操作类型
        """
        self.kb_id = kb_id
        self.user_id = user_id
        self.operation_type = operation_type

    def add_stage(self, stage_name: str, **kwargs):
        """添加处理阶段

        Args:
            stage_name: 阶段名称
            **kwargs: 阶段相关的额外信息
        """
        current_time = time.time()
        stage_info = {
            "stage": stage_name,
            "timestamp": current_time,
            "duration_from_start": current_time - self.start_time,
            **kwargs,
        }
        self.stages.append(stage_info)

    def update_performance_metrics(self, **metrics):
        """更新性能指标

        Args:
            **metrics: 性能指标键值对
        """
        self.performance_metrics.update(metrics)

    def get_total_duration(self) -> float:
        """获取总耗时

        Returns:
            float: 总耗时(秒)
        """
        return time.time() - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式

        Returns:
            Dict[str, Any]: 上下文信息字典
        """
        return {
            "trace_id": self.trace_id,
            "kb_id": self.kb_id,
            "user_id": self.user_id,
            "operation_type": self.operation_type,
            "start_time": self.start_time,
            "total_duration": self.get_total_duration(),
            "stages": self.stages,
            "performance_metrics": self.performance_metrics,
        }


class Logger:
    """增强的日志记录器

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
                log_data = {
                    "timestamp": self.formatTime(record, self.datefmt),
                    "level": record.levelname,
                    "trace_id": getattr(record, "trace_id", "无"),
                    "module": record.module,
                    "line": record.lineno,
                    "message": record.getMessage(),
                }

                # 添加额外字段
                for key, value in getattr(record, "extra_fields", {}).items():
                    if key not in log_data:
                        log_data[key] = value

                return json.dumps(log_data, ensure_ascii=False)

        json_formatter = JsonFormatter()

        # 创建控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(text_formatter)
        logger.addHandler(console_handler)

        # 创建文件处理器 - 普通日志
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        file_handler = RotatingFileHandler(
            log_dir / "app.log",
            maxBytes=10485760,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(text_formatter)
        logger.addHandler(file_handler)

        # 创建文件处理器 - JSON格式日志
        json_handler = RotatingFileHandler(
            log_dir / "app.json.log",
            maxBytes=10485760,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        json_handler.setFormatter(json_formatter)
        logger.addHandler(json_handler)

        return logger

    @staticmethod
    def _get_trace_context() -> Dict[str, Any]:
        """获取当前请求的追踪上下文"""
        try:
            context = trace_context.get()
            if not context:
                # 如果上下文为空，创建新的上下文
                context = {
                    "trace_id": f"trace-{uuid.uuid4().hex[:8]}",
                    "start_time": time.time(),
                }
                trace_context.set(context)
            return context
        except Exception:
            # 如果获取上下文失败，返回默认值
            return {
                "trace_id": f"fallback-{uuid.uuid4().hex[:8]}",
                "start_time": time.time(),
            }

    @classmethod
    def init_trace(cls, trace_id: Optional[str] = None, **kwargs) -> str:
        """初始化请求追踪

        Args:
            trace_id: 可选的追踪ID，如果不提供则自动生成
            **kwargs: 其他要添加到追踪上下文的键值对

        Returns:
            str: 追踪ID
        """
        if not trace_id:
            trace_id = f"trace-{uuid.uuid4().hex[:8]}"

        context = {"trace_id": trace_id, "start_time": time.time(), **kwargs}

        # 如果是RAG相关操作，创建RAG追踪上下文
        if any(key in kwargs for key in ["kb_id", "operation_type", "rag_context"]):
            rag_context = RAGTraceContext(trace_id)
            if "kb_id" in kwargs:
                rag_context.set_kb_context(
                    kb_id=kwargs.get("kb_id"),
                    user_id=kwargs.get("user_id"),
                    operation_type=kwargs.get("operation_type"),
                )
            context["rag_context"] = rag_context

        trace_context.set(context)
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
        if not trace_id:
            trace_id = f"rag-{uuid.uuid4().hex[:8]}"

        rag_context = RAGTraceContext(trace_id)
        rag_context.set_kb_context(kb_id, user_id, operation_type)

        context = {
            "trace_id": trace_id,
            "start_time": time.time(),
            "kb_id": kb_id,
            "user_id": user_id,
            "operation_type": operation_type,
            "rag_context": rag_context,
        }

        trace_context.set(context)
        return trace_id

    @classmethod
    def get_rag_context(cls) -> Optional[RAGTraceContext]:
        """获取当前的RAG追踪上下文

        Returns:
            Optional[RAGTraceContext]: RAG追踪上下文，如果不存在则返回None
        """
        context = cls._get_trace_context()
        return context.get("rag_context")

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
            # 添加最终阶段
            rag_context.add_stage(
                "trace_finalized", final_duration=rag_context.get_total_duration()
            )

            # 记录追踪完成日志
            cls.info(
                "RAG链路追踪完成",
                extra={
                    "trace_id": rag_context.trace_id,
                    "kb_id": rag_context.kb_id,
                    "operation_type": rag_context.operation_type,
                    "total_duration": rag_context.get_total_duration(),
                    "stages_count": len(rag_context.stages),
                    "performance_metrics": rag_context.performance_metrics,
                },
            )

            return rag_context.to_dict()
        return {}

    @classmethod
    def set_rag_operation_context(cls, operation_type: str, **context_data):
        """设置RAG操作上下文信息

        Args:
            operation_type: 操作类型
            **context_data: 上下文数据
        """
        rag_context = cls.get_rag_context()
        if rag_context:
            rag_context.operation_type = operation_type
            rag_context.update_performance_metrics(**context_data)

            cls.debug(
                f"设置RAG操作上下文: {operation_type}",
                extra={"operation_type": operation_type, "context_data": context_data},
            )

    @classmethod
    def get_trace_id(cls) -> str:
        """获取当前请求的追踪ID"""
        return cls._get_trace_context().get("trace_id", "无追踪ID")

    @classmethod
    def _log(cls, level: int, message: str, extra: Dict[str, Any] = None):
        """记录日志的内部方法

        Args:
            level: 日志级别
            message: 日志消息
            extra: 额外的日志字段
        """
        context = cls._get_trace_context()
        trace_id = context.get("trace_id", "无追踪ID")

        # 准备额外字段
        extra_fields = {
            "trace_id": trace_id,
            "thread_id": threading.get_ident(),
            "extra_fields": extra or {},
        }

        # 添加RAG上下文信息
        rag_context = context.get("rag_context")
        if rag_context:
            extra_fields["rag_context"] = {
                "kb_id": rag_context.kb_id,
                "user_id": rag_context.user_id,
                "operation_type": rag_context.operation_type,
                "total_duration": rag_context.get_total_duration(),
                "stage_count": len(rag_context.stages),
            }

        if extra:
            extra_fields["extra_fields"].update(extra)

        # 获取调用者信息
        logger = cls.get_logger()
        logger.log(level, message, extra=extra_fields)

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

    @classmethod
    def api_request(cls, method: str, path: str, params: Dict = None, **kwargs):
        """记录API请求日志

        Args:
            method: HTTP方法
            path: 请求路径
            params: 请求参数
            **kwargs: 额外的日志字段
        """
        cls.info(
            f"收到API请求: {method} {path}",
            api_method=method,
            api_path=path,
            api_params=params or {},
            **kwargs,
        )

    @classmethod
    def api_response(
        cls, method: str, path: str, status_code: int, process_time: float, **kwargs
    ):
        """记录API响应日志

        Args:
            method: HTTP方法
            path: 请求路径
            status_code: 响应状态码
            process_time: 处理时间(秒)
            **kwargs: 额外的日志字段
        """
        cls.info(
            f"API响应: {method} {path} - 状态码: {status_code} - 处理时间: {process_time:.2f}秒",
            api_method=method,
            api_path=path,
            status_code=status_code,
            process_time=process_time,
            **kwargs,
        )

    @classmethod
    def service_call(cls, service: str, method: str, **kwargs):
        """记录服务调用日志

        Args:
            service: 服务名称
            method: 方法名称
            **kwargs: 额外的日志字段
        """
        cls.debug(
            f"调用服务: {service}.{method}", service=service, method=method, **kwargs
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
        level = cls.info if success else cls.error
        level(
            f"服务调用结果: {service}.{method} - {'成功' if success else '失败'} - 耗时: {process_time:.2f}秒",
            service=service,
            method=method,
            success=success,
            process_time=process_time,
            **kwargs,
        )

    @classmethod
    def database_query(cls, query: str, params: Any = None, **kwargs):
        """记录数据库查询日志

        Args:
            query: SQL查询
            params: 查询参数
            **kwargs: 额外的日志字段
        """
        cls.debug(f"数据库查询: {query}", query=query, params=params, **kwargs)

    @classmethod
    def database_result(
        cls,
        query: str,
        success: bool,
        process_time: float,
        row_count: int = None,
        **kwargs,
    ):
        """记录数据库查询结果日志

        Args:
            query: SQL查询
            success: 是否成功
            process_time: 处理时间(秒)
            row_count: 影响的行数
            **kwargs: 额外的日志字段
        """
        row_info = f" - 影响行数: {row_count}" if row_count is not None else ""
        cls.debug(
            f"数据库查询结果: {'成功' if success else '失败'} - 耗时: {process_time:.2f}秒{row_info}",
            query=query,
            success=success,
            process_time=process_time,
            row_count=row_count,
            **kwargs,
        )

    @classmethod
    def rag_operation(cls, operation: str, kb_id: int = None, **kwargs):
        """记录RAG操作日志

        Args:
            operation: 操作类型
            kb_id: 知识库ID
            **kwargs: 额外的日志字段
        """
        kb_info = f" - 知识库ID: {kb_id}" if kb_id is not None else ""
        cls.info(
            f"RAG操作: {operation}{kb_info}", operation=operation, kb_id=kb_id, **kwargs
        )

    @classmethod
    def websocket_event(
        cls, event_type: str, chat_id: int = None, client_id: str = None, **kwargs
    ):
        """记录WebSocket事件日志

        Args:
            event_type: 事件类型
            chat_id: 聊天ID
            client_id: 客户端ID
            **kwargs: 额外的日志字段
        """
        chat_info = f" - 聊天ID: {chat_id}" if chat_id is not None else ""
        client_info = f" - 客户端ID: {client_id}" if client_id is not None else ""
        cls.info(
            f"WebSocket事件: {event_type}{chat_info}{client_info}",
            event_type=event_type,
            chat_id=chat_id,
            client_id=client_id,
            **kwargs,
        )

    # ==================== RAG特定日志方法 ====================

    @classmethod
    def rag_api_request(
        cls,
        endpoint: str,
        method: str = "POST",
        kb_id: int = None,
        user_id: int = None,
        params: Dict = None,
        **kwargs,
    ):
        """记录RAG API请求日志

        Args:
            endpoint: API端点
            method: HTTP方法
            kb_id: 知识库ID
            user_id: 用户ID
            params: 请求参数
            **kwargs: 额外的日志字段
        """
        kb_info = f" - 知识库ID: {kb_id}" if kb_id is not None else ""
        user_info = f" - 用户ID: {user_id}" if user_id is not None else ""
        cls.info(
            f"RAG API请求: {method} {endpoint}{kb_info}{user_info}",
            rag_operation_type="api_request",
            api_endpoint=endpoint,
            api_method=method,
            kb_id=kb_id,
            user_id=user_id,
            api_params=params or {},
            **kwargs,
        )

    @classmethod
    def rag_api_response(
        cls,
        endpoint: str,
        method: str = "POST",
        status_code: int = 200,
        process_time: float = 0.0,
        kb_id: int = None,
        result_summary: Dict = None,
        **kwargs,
    ):
        """记录RAG API响应日志

        Args:
            endpoint: API端点
            method: HTTP方法
            status_code: 响应状态码
            process_time: 处理时间(秒)
            kb_id: 知识库ID
            result_summary: 结果摘要
            **kwargs: 额外的日志字段
        """
        kb_info = f" - 知识库ID: {kb_id}" if kb_id is not None else ""
        cls.info(
            f"RAG API响应: {method} {endpoint} - 状态码: {status_code} - 处理时间: {process_time:.2f}秒{kb_info}",
            rag_operation_type="api_response",
            api_endpoint=endpoint,
            api_method=method,
            status_code=status_code,
            process_time=process_time,
            kb_id=kb_id,
            result_summary=result_summary or {},
            **kwargs,
        )

    @classmethod
    def rag_api_error(
        cls,
        endpoint: str,
        method: str = "POST",
        error: str = "",
        kb_id: int = None,
        user_id: int = None,
        **kwargs,
    ):
        """记录RAG API错误日志

        Args:
            endpoint: API端点
            method: HTTP方法
            error: 错误信息
            kb_id: 知识库ID
            user_id: 用户ID
            **kwargs: 额外的日志字段
        """
        kb_info = f" - 知识库ID: {kb_id}" if kb_id is not None else ""
        user_info = f" - 用户ID: {user_id}" if user_id is not None else ""
        cls.error(
            f"RAG API错误: {method} {endpoint}{kb_info}{user_info} - 错误: {error}",
            rag_operation_type="api_error",
            api_endpoint=endpoint,
            api_method=method,
            error_message=error,
            kb_id=kb_id,
            user_id=user_id,
            **kwargs,
        )

    @classmethod
    def rag_training_start(
        cls, kb_id: int, document_count: int, config: Dict = None, **kwargs
    ):
        """记录RAG训练开始日志

        Args:
            kb_id: 知识库ID
            document_count: 文档数量
            config: 训练配置
            **kwargs: 额外的日志字段
        """
        cls.info(
            f"RAG训练开始: 知识库ID {kb_id} - 文档数量: {document_count}",
            rag_operation_type="training_start",
            kb_id=kb_id,
            document_count=document_count,
            training_config=config or {},
            **kwargs,
        )

    @classmethod
    def rag_training_complete(
        cls,
        kb_id: int,
        success: bool,
        duration: float,
        result_summary: Dict = None,
        **kwargs,
    ):
        """记录RAG训练完成日志

        Args:
            kb_id: 知识库ID
            success: 是否成功
            duration: 训练耗时(秒)
            result_summary: 结果摘要
            **kwargs: 额外的日志字段
        """
        status = "成功" if success else "失败"
        level = cls.info if success else cls.error
        level(
            f"RAG训练{status}: 知识库ID {kb_id} - 耗时: {duration:.2f}秒",
            rag_operation_type="training_complete",
            kb_id=kb_id,
            training_success=success,
            training_duration=duration,
            result_summary=result_summary or {},
            **kwargs,
        )

    @classmethod
    def rag_document_processing_start(
        cls, kb_id: int, document_count: int, config: Dict = None, **kwargs
    ):
        """记录RAG文档处理开始日志

        Args:
            kb_id: 知识库ID
            document_count: 文档数量
            config: 处理配置
            **kwargs: 额外的日志字段
        """
        cls.info(
            f"RAG文档处理开始: 知识库ID {kb_id} - 文档数量: {document_count}",
            rag_operation_type="document_processing_start",
            kb_id=kb_id,
            document_count=document_count,
            processing_config=config or {},
            **kwargs,
        )

    @classmethod
    def rag_document_start(
        cls,
        kb_id: int,
        document_id: int,
        document_title: str = "",
        progress: Dict = None,
        **kwargs,
    ):
        """记录RAG单个文档处理开始日志

        Args:
            kb_id: 知识库ID
            document_id: 文档ID
            document_title: 文档标题
            progress: 进度信息
            **kwargs: 额外的日志字段
        """
        progress_info = ""
        if progress and "current" in progress and "total" in progress:
            progress_info = f" - 进度: {progress['current']}/{progress['total']}"

        cls.info(
            f"RAG文档处理: 知识库ID {kb_id} - 文档ID {document_id} - 标题: {document_title}{progress_info}",
            rag_operation_type="document_start",
            kb_id=kb_id,
            document_id=document_id,
            document_title=document_title,
            progress=progress or {},
            **kwargs,
        )

    @classmethod
    def rag_document_error(
        cls,
        kb_id: int,
        document_id: int,
        stage: str,
        error: str,
        progress: Dict = None,
        **kwargs,
    ):
        """记录RAG文档处理错误日志

        Args:
            kb_id: 知识库ID
            document_id: 文档ID
            stage: 处理阶段
            error: 错误信息
            progress: 进度信息
            **kwargs: 额外的日志字段
        """
        progress_info = ""
        if progress and "current" in progress and "total" in progress:
            progress_info = f" - 进度: {progress['current']}/{progress['total']}"

        cls.error(
            f"RAG文档处理错误: 知识库ID {kb_id} - 文档ID {document_id} - 阶段: {stage} - 错误: {error}{progress_info}",
            rag_operation_type="document_error",
            kb_id=kb_id,
            document_id=document_id,
            processing_stage=stage,
            error_message=error,
            progress=progress or {},
            **kwargs,
        )

    @classmethod
    def rag_extraction_start(
        cls, document_id: int, file_path: str, file_type: str = "", **kwargs
    ):
        """记录RAG文档提取开始日志

        Args:
            document_id: 文档ID
            file_path: 文件路径
            file_type: 文件类型
            **kwargs: 额外的日志字段
        """
        cls.debug(
            f"RAG文档提取开始: 文档ID {document_id} - 文件: {file_path} - 类型: {file_type}",
            rag_operation_type="extraction_start",
            document_id=document_id,
            file_path=file_path,
            file_type=file_type,
            **kwargs,
        )

    @classmethod
    def rag_extraction_success(
        cls, document_id: int, content_length: int, extraction_time: float, **kwargs
    ):
        """记录RAG文档提取成功日志

        Args:
            document_id: 文档ID
            content_length: 内容长度
            extraction_time: 提取耗时(秒)
            **kwargs: 额外的日志字段
        """
        cls.debug(
            f"RAG文档提取成功: 文档ID {document_id} - 内容长度: {content_length} - 耗时: {extraction_time:.2f}秒",
            rag_operation_type="extraction_success",
            document_id=document_id,
            content_length=content_length,
            extraction_time=extraction_time,
            **kwargs,
        )

    @classmethod
    def rag_chunking_start(
        cls, document_id: int, content_length: int, chunk_size: int, **kwargs
    ):
        """记录RAG文本分块开始日志

        Args:
            document_id: 文档ID
            content_length: 内容长度
            chunk_size: 分块大小
            **kwargs: 额外的日志字段
        """
        cls.debug(
            f"RAG文本分块开始: 文档ID {document_id} - 内容长度: {content_length} - 分块大小: {chunk_size}",
            rag_operation_type="chunking_start",
            document_id=document_id,
            content_length=content_length,
            chunk_size=chunk_size,
            **kwargs,
        )

    @classmethod
    def rag_chunking_success(
        cls, document_id: int, chunk_count: int, chunking_time: float, **kwargs
    ):
        """记录RAG文本分块成功日志

        Args:
            document_id: 文档ID
            chunk_count: 分块数量
            chunking_time: 分块耗时(秒)
            **kwargs: 额外的日志字段
        """
        cls.debug(
            f"RAG文本分块成功: 文档ID {document_id} - 分块数量: {chunk_count} - 耗时: {chunking_time:.2f}秒",
            rag_operation_type="chunking_success",
            document_id=document_id,
            chunk_count=chunk_count,
            chunking_time=chunking_time,
            **kwargs,
        )

    @classmethod
    def rag_embedding_start(
        cls,
        document_id: int = None,
        chunk_count: int = 0,
        model: str = "",
        batch_size: int = 0,
        **kwargs,
    ):
        """记录RAG向量化开始日志

        Args:
            document_id: 文档ID
            chunk_count: 分块数量
            model: 向量化模型
            batch_size: 批处理大小
            **kwargs: 额外的日志字段
        """
        doc_info = f"文档ID {document_id} - " if document_id else ""
        cls.debug(
            f"RAG向量化开始: {doc_info}分块数量: {chunk_count} - 模型: {model} - 批大小: {batch_size}",
            rag_operation_type="embedding_start",
            document_id=document_id,
            chunk_count=chunk_count,
            embedding_model=model,
            batch_size=batch_size,
            **kwargs,
        )

    @classmethod
    def rag_embedding_batch(
        cls,
        batch_num: int,
        total_batches: int,
        batch_size: int,
        model: str = "",
        progress: Dict = None,
        **kwargs,
    ):
        """记录RAG向量化批处理日志

        Args:
            batch_num: 当前批次号
            total_batches: 总批次数
            batch_size: 批处理大小
            model: 向量化模型
            progress: 进度信息
            **kwargs: 额外的日志字段
        """
        cls.debug(
            f"RAG向量化批处理: 批次 {batch_num}/{total_batches} - 批大小: {batch_size} - 模型: {model}",
            rag_operation_type="embedding_batch",
            batch_number=batch_num,
            total_batches=total_batches,
            batch_size=batch_size,
            embedding_model=model,
            progress=progress or {},
            **kwargs,
        )

    @classmethod
    def rag_embedding_success(
        cls,
        document_id: int = None,
        embedding_count: int = 0,
        embedding_time: float = 0.0,
        model: str = "",
        **kwargs,
    ):
        """记录RAG向量化成功日志

        Args:
            document_id: 文档ID
            embedding_count: 向量数量
            embedding_time: 向量化耗时(秒)
            model: 向量化模型
            **kwargs: 额外的日志字段
        """
        doc_info = f"文档ID {document_id} - " if document_id else ""
        cls.debug(
            f"RAG向量化成功: {doc_info}向量数量: {embedding_count} - 耗时: {embedding_time:.2f}秒 - 模型: {model}",
            rag_operation_type="embedding_success",
            document_id=document_id,
            embedding_count=embedding_count,
            embedding_time=embedding_time,
            embedding_model=model,
            **kwargs,
        )

    @classmethod
    def rag_query_start(
        cls,
        kb_id: int,
        query: str,
        method: str = "",
        params: Dict = None,
        user_id: int = None,
        **kwargs,
    ):
        """记录RAG查询开始日志

        Args:
            kb_id: 知识库ID
            query: 查询内容
            method: 检索方法
            params: 查询参数
            user_id: 用户ID
            **kwargs: 额外的日志字段
        """
        query_preview = query[:100] + "..." if len(query) > 100 else query
        user_info = f" - 用户ID: {user_id}" if user_id else ""
        cls.info(
            f"RAG查询开始: 知识库ID {kb_id} - 查询: '{query_preview}' - 方法: {method}{user_info}",
            rag_operation_type="query_start",
            kb_id=kb_id,
            query=query,
            query_method=method,
            query_params=params or {},
            user_id=user_id,
            **kwargs,
        )

    @classmethod
    def rag_query_complete(
        cls,
        kb_id: int,
        query: str,
        success: bool,
        duration: float,
        result_count: int = 0,
        **kwargs,
    ):
        """记录RAG查询完成日志

        Args:
            kb_id: 知识库ID
            query: 查询内容
            success: 是否成功
            duration: 查询耗时(秒)
            result_count: 结果数量
            **kwargs: 额外的日志字段
        """
        query_preview = query[:50] + "..." if len(query) > 50 else query
        status = "成功" if success else "失败"
        level = cls.info if success else cls.error
        level(
            f"RAG查询{status}: 知识库ID {kb_id} - 查询: '{query_preview}' - 结果数: {result_count} - 耗时: {duration:.2f}秒",
            rag_operation_type="query_complete",
            kb_id=kb_id,
            query=query,
            query_success=success,
            query_duration=duration,
            result_count=result_count,
            **kwargs,
        )

    @classmethod
    def rag_retrieval_result(
        cls,
        kb_id: int,
        query: str,
        result_count: int,
        scores: List[float] = None,
        method: str = "",
        **kwargs,
    ):
        """记录RAG检索结果日志

        Args:
            kb_id: 知识库ID
            query: 查询内容
            result_count: 结果数量
            scores: 相关性分数列表
            method: 检索方法
            **kwargs: 额外的日志字段
        """
        query_preview = query[:50] + "..." if len(query) > 50 else query
        avg_score = sum(scores) / len(scores) if scores else 0.0
        max_score = max(scores) if scores else 0.0

        cls.debug(
            f"RAG检索结果: 知识库ID {kb_id} - 查询: '{query_preview}' - 方法: {method} - 结果数: {result_count} - 平均分: {avg_score:.3f} - 最高分: {max_score:.3f}",
            rag_operation_type="retrieval_result",
            kb_id=kb_id,
            query=query,
            retrieval_method=method,
            result_count=result_count,
            scores=scores or [],
            avg_score=avg_score,
            max_score=max_score,
            **kwargs,
        )

    @classmethod
    def rag_permission_check(
        cls,
        kb_id: int,
        user_id: int,
        required_permission: str,
        granted: bool = True,
        **kwargs,
    ):
        """记录RAG权限检查日志

        Args:
            kb_id: 知识库ID
            user_id: 用户ID
            required_permission: 所需权限
            granted: 是否授权
            **kwargs: 额外的日志字段
        """
        status = "通过" if granted else "拒绝"
        level = cls.debug if granted else cls.warning
        level(
            f"RAG权限检查{status}: 知识库ID {kb_id} - 用户ID {user_id} - 所需权限: {required_permission}",
            rag_operation_type="permission_check",
            kb_id=kb_id,
            user_id=user_id,
            required_permission=required_permission,
            permission_granted=granted,
            **kwargs,
        )

    @classmethod
    def rag_service_start(
        cls, service: str, method: str, kb_id: int = None, user_id: int = None, **kwargs
    ):
        """记录RAG服务调用开始日志

        Args:
            service: 服务名称
            method: 方法名称
            kb_id: 知识库ID
            user_id: 用户ID
            **kwargs: 额外的日志字段
        """
        kb_info = f" - 知识库ID: {kb_id}" if kb_id else ""
        user_info = f" - 用户ID: {user_id}" if user_id else ""
        cls.debug(
            f"RAG服务调用开始: {service}.{method}{kb_info}{user_info}",
            rag_operation_type="service_start",
            service=service,
            method=method,
            kb_id=kb_id,
            user_id=user_id,
            **kwargs,
        )

    @classmethod
    def rag_service_success(
        cls,
        service: str,
        method: str,
        duration: float = 0.0,
        result_summary: Dict = None,
        **kwargs,
    ):
        """记录RAG服务调用成功日志

        Args:
            service: 服务名称
            method: 方法名称
            duration: 执行耗时(秒)
            result_summary: 结果摘要
            **kwargs: 额外的日志字段
        """
        cls.debug(
            f"RAG服务调用成功: {service}.{method} - 耗时: {duration:.2f}秒",
            rag_operation_type="service_success",
            service=service,
            method=method,
            service_duration=duration,
            result_summary=result_summary or {},
            **kwargs,
        )

    @classmethod
    def rag_service_error(
        cls, service: str, method: str, error: str, duration: float = 0.0, **kwargs
    ):
        """记录RAG服务调用错误日志

        Args:
            service: 服务名称
            method: 方法名称
            error: 错误信息
            duration: 执行耗时(秒)
            **kwargs: 额外的日志字段
        """
        cls.error(
            f"RAG服务调用失败: {service}.{method} - 错误: {error} - 耗时: {duration:.2f}秒",
            rag_operation_type="service_error",
            service=service,
            method=method,
            error_message=error,
            service_duration=duration,
            **kwargs,
        )

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
        memory_mb = memory_usage / 1024 / 1024 if memory_usage > 0 else 0
        cls.debug(
            f"RAG性能指标: {operation} - 耗时: {duration:.2f}秒 - 内存: {memory_mb:.1f}MB - CPU: {cpu_usage:.1f}%{kb_info}",
            rag_operation_type="performance_metrics",
            operation=operation,
            duration=duration,
            memory_usage=memory_usage,
            memory_mb=memory_mb,
            cpu_usage=cpu_usage,
            kb_id=kb_id,
            **kwargs,
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
            f"RAG重试尝试: {operation} - 尝试 {attempt}/{max_retries}",
            rag_operation_type="retry_attempt",
            operation=operation,
            attempt_number=attempt,
            max_retries=max_retries,
            **kwargs,
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
            **kwargs,
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
            **kwargs,
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
            **kwargs,
        )

    @classmethod
    def rag_performance_metrics(cls, operation: str, duration: float, **metrics):
        """记录RAG性能指标日志

        Args:
            operation: 操作名称
            duration: 操作耗时(秒)
            **metrics: 其他性能指标
        """
        cls.debug(
            f"RAG性能指标: {operation} - 耗时: {duration:.3f}秒",
            rag_operation_type="performance_metrics",
            operation=operation,
            duration=duration,
            **metrics,
        )

    @classmethod
    def rag_document_processing_complete(
        cls,
        kb_id: int,
        success: bool,
        duration: float,
        processed_count: int = 0,
        failed_count: int = 0,
        result_summary: Dict = None,
        **kwargs,
    ):
        """记录RAG文档处理完成日志

        Args:
            kb_id: 知识库ID
            success: 是否成功
            duration: 处理耗时(秒)
            processed_count: 成功处理的文档数量
            failed_count: 处理失败的文档数量
            result_summary: 结果摘要
            **kwargs: 额外的日志字段
        """
        status = "成功" if success else "失败"
        level = cls.info if success else cls.error
        level(
            f"RAG文档处理{status}: 知识库ID {kb_id} - 耗时: {duration:.2f}秒 - 成功: {processed_count} - 失败: {failed_count}",
            rag_operation_type="document_processing_complete",
            kb_id=kb_id,
            processing_success=success,
            processing_duration=duration,
            processed_count=processed_count,
            failed_count=failed_count,
            result_summary=result_summary or {},
            **kwargs,
        )

    @classmethod
    def rag_document_complete(
        cls,
        kb_id: int,
        document_id: int,
        success: bool,
        duration: float,
        stages_completed: List[str] = None,
        error: str = "",
        **kwargs,
    ):
        """记录RAG单个文档处理完成日志

        Args:
            kb_id: 知识库ID
            document_id: 文档ID
            success: 是否成功
            duration: 处理耗时(秒)
            stages_completed: 完成的处理阶段列表
            error: 错误信息（如果失败）
            **kwargs: 额外的日志字段
        """
        status = "成功" if success else "失败"
        level = cls.info if success else cls.error
        error_info = f" - 错误: {error}" if error else ""
        stages_info = (
            f" - 完成阶段: {len(stages_completed or [])}" if stages_completed else ""
        )

        level(
            f"RAG文档处理{status}: 知识库ID {kb_id} - 文档ID {document_id} - 耗时: {duration:.2f}秒{stages_info}{error_info}",
            rag_operation_type="document_complete",
            kb_id=kb_id,
            document_id=document_id,
            processing_success=success,
            processing_duration=duration,
            stages_completed=stages_completed or [],
            error_message=error,
            **kwargs,
        )

    @classmethod
    def rag_index_build_start(
        cls,
        kb_id: int,
        index_type: str,
        document_count: int = 0,
        config: Dict = None,
        **kwargs,
    ):
        """记录RAG索引构建开始日志

        Args:
            kb_id: 知识库ID
            index_type: 索引类型
            document_count: 文档数量
            config: 索引配置
            **kwargs: 额外的日志字段
        """
        cls.info(
            f"RAG索引构建开始: 知识库ID {kb_id} - 索引类型: {index_type} - 文档数量: {document_count}",
            rag_operation_type="index_build_start",
            kb_id=kb_id,
            index_type=index_type,
            document_count=document_count,
            index_config=config or {},
            **kwargs,
        )

    @classmethod
    def rag_index_build_complete(
        cls,
        kb_id: int,
        index_type: str,
        success: bool,
        duration: float,
        index_size: int = 0,
        **kwargs,
    ):
        """记录RAG索引构建完成日志

        Args:
            kb_id: 知识库ID
            index_type: 索引类型
            success: 是否成功
            duration: 构建耗时(秒)
            index_size: 索引大小
            **kwargs: 额外的日志字段
        """
        status = "成功" if success else "失败"
        level = cls.info if success else cls.error
        level(
            f"RAG索引构建{status}: 知识库ID {kb_id} - 索引类型: {index_type} - 耗时: {duration:.2f}秒 - 索引大小: {index_size}",
            rag_operation_type="index_build_complete",
            kb_id=kb_id,
            index_type=index_type,
            build_success=success,
            build_duration=duration,
            index_size=index_size,
            **kwargs,
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
