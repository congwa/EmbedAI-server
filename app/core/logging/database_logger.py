"""
数据库相关日志记录模块
"""
from typing import Any
from .base_logger import BaseLogger


class DatabaseLogger(BaseLogger):
    """数据库相关日志记录器"""

    @classmethod
    def database_query(cls, query: str, params: Any = None, **kwargs):
        """记录数据库查询日志

        Args:
            query: SQL查询
            params: 查询参数
            **kwargs: 额外的日志字段
        """
        # 截取查询语句的前100个字符用于日志
        query_preview = query[:100] + "..." if len(query) > 100 else query
        params_info = f" - 参数: {params}" if params else ""
        
        cls.debug(
            f"数据库查询: {query_preview}{params_info}",
            db_query=query,
            db_params=params,
            **kwargs
        )

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
        query_preview = query[:100] + "..." if len(query) > 100 else query
        status = "成功" if success else "失败"
        level = cls.debug if success else cls.error
        row_info = f" - 影响行数: {row_count}" if row_count is not None else ""
        
        level(
            f"数据库查询{status}: {query_preview} - 耗时: {process_time:.3f}秒{row_info}",
            db_query=query,
            db_success=success,
            db_process_time=process_time,
            db_row_count=row_count,
            **kwargs
        )
