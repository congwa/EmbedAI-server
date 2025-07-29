"""
API相关日志记录模块
"""
from typing import Dict, Any
from .base_logger import BaseLogger


class APILogger(BaseLogger):
    """API相关日志记录器"""

    @classmethod
    def api_request(cls, method: str, path: str, params: Dict = None, **kwargs):
        """记录API请求日志

        Args:
            method: HTTP方法
            path: 请求路径
            params: 请求参数
            **kwargs: 额外的日志字段
        """
        params_info = f" - 参数: {params}" if params else ""
        cls.info(
            f"API请求: {method} {path}{params_info}",
            api_method=method,
            api_path=path,
            api_params=params,
            **kwargs
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
        status_text = "成功" if 200 <= status_code < 300 else "失败"
        level = cls.info if 200 <= status_code < 300 else cls.error
        level(
            f"API响应: {method} {path} - 状态码: {status_code} - {status_text} - 耗时: {process_time:.3f}秒",
            api_method=method,
            api_path=path,
            status_code=status_code,
            process_time=process_time,
            **kwargs
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
        chat_info = f" - 聊天ID: {chat_id}" if chat_id else ""
        client_info = f" - 客户端ID: {client_id}" if client_id else ""
        
        cls.debug(
            f"WebSocket事件: {event_type}{chat_info}{client_info}",
            websocket_event=event_type,
            chat_id=chat_id,
            client_id=client_id,
            **kwargs
        )
