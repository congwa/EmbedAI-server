import logging
import sys
import uuid
import json
import time
import threading
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any, Union
from contextvars import ContextVar
from app.core.config import settings

# 创建上下文变量，用于存储请求跟踪信息
trace_context: ContextVar[Dict[str, Any]] = ContextVar('trace_context', default={})

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
            '%(asctime)s [%(levelname)s] [%(trace_id)s] [%(module)s:%(lineno)d] - %(message)s'
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
                    "message": record.getMessage()
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
            encoding="utf-8"
        )
        file_handler.setFormatter(text_formatter)
        logger.addHandler(file_handler)
        
        # 创建文件处理器 - JSON格式日志
        json_handler = RotatingFileHandler(
            log_dir / "app.json.log",
            maxBytes=10485760,  # 10MB
            backupCount=5,
            encoding="utf-8"
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
                    "start_time": time.time()
                }
                trace_context.set(context)
            return context
        except Exception:
            # 如果获取上下文失败，返回默认值
            return {
                "trace_id": f"fallback-{uuid.uuid4().hex[:8]}",
                "start_time": time.time()
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
            
        context = {
            "trace_id": trace_id,
            "start_time": time.time(),
            **kwargs
        }
        trace_context.set(context)
        return trace_id
    
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
            "extra_fields": extra or {}
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
            **kwargs
        )
        
    @classmethod
    def api_response(cls, method: str, path: str, status_code: int, 
                     process_time: float, **kwargs):
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
            **kwargs
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
            f"调用服务: {service}.{method}",
            service=service,
            method=method,
            **kwargs
        )
        
    @classmethod
    def service_result(cls, service: str, method: str, 
                       success: bool, process_time: float, **kwargs):
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
            **kwargs
        )
        
    @classmethod
    def database_query(cls, query: str, params: Any = None, **kwargs):
        """记录数据库查询日志
        
        Args:
            query: SQL查询
            params: 查询参数
            **kwargs: 额外的日志字段
        """
        cls.debug(
            f"数据库查询: {query}",
            query=query,
            params=params,
            **kwargs
        )
        
    @classmethod
    def database_result(cls, query: str, success: bool, 
                        process_time: float, row_count: int = None, **kwargs):
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
            **kwargs
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
            f"RAG操作: {operation}{kb_info}",
            operation=operation,
            kb_id=kb_id,
            **kwargs
        )
        
    @classmethod
    def websocket_event(cls, event_type: str, chat_id: int = None, 
                        client_id: str = None, **kwargs):
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
            **kwargs
        ) 