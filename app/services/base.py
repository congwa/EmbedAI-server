"""服务层基类

提供统一的异常处理和通用功能
"""

from typing import Callable, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app.core.logger import Logger
from app.core.exceptions import (
    APIException,
    SystemException,
    ResourceNotFoundException,
    PermissionDeniedException,
    BusinessException
)
from fastapi import status


class BaseService:
    """服务基类，提供统一的异常处理和通用功能"""
    
    def __init__(self, db: AsyncSession):
        """初始化服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    async def handle_db_operation(self, operation: Callable, error_message: str = "数据库操作失败") -> Any:
        """统一处理数据库操作异常
        
        Args:
            operation: 要执行的数据库操作函数
            error_message: 自定义错误消息
            
        Returns:
            操作结果
            
        Raises:
            SystemException: 当数据库操作失败时
        """
        try:
            return await operation()
        except SQLAlchemyError as e:
            Logger.error(f"数据库操作失败: {str(e)}")
            raise SystemException(
                message=error_message,
                error_code="DATABASE_ERROR"
            )
        except Exception as e:
            Logger.error(f"数据库操作异常: {str(e)}")
            raise SystemException(
                message=error_message,
                error_code="UNKNOWN_DATABASE_ERROR"
            )
    
    async def check_resource_exists(
        self, 
        resource: Any, 
        resource_name: str = "资源",
        resource_id: Any = None
    ) -> Any:
        """检查资源是否存在
        
        Args:
            resource: 资源对象
            resource_name: 资源名称
            resource_id: 资源ID
            
        Returns:
            资源对象
            
        Raises:
            ResourceNotFoundException: 当资源不存在时
        """
        if resource is None:
            raise ResourceNotFoundException(resource_name, resource_id)
        return resource
    
    def check_permission(
        self, 
        condition: bool, 
        message: str = "权限不足",
        required_permission: str = None
    ) -> None:
        """检查权限条件
        
        Args:
            condition: 权限检查条件
            message: 权限错误消息
            required_permission: 需要的权限
            
        Raises:
            PermissionDeniedException: 当权限不足时
        """
        if not condition:
            raise PermissionDeniedException(message, required_permission)
    
    def validate_business_rule(
        self, 
        condition: bool, 
        message: str,
        data: Any = None
    ) -> None:
        """验证业务规则
        
        Args:
            condition: 业务规则条件
            message: 业务错误消息
            data: 额外的业务数据
            
        Raises:
            BusinessException: 当业务规则验证失败时
        """
        if not condition:
            raise BusinessException(message, data)
    
    async def safe_execute(
        self, 
        operation: Callable,
        error_message: str = "操作失败",
        error_code: str = None
    ) -> Any:
        """安全执行操作，统一异常处理
        
        Args:
            operation: 要执行的操作函数
            error_message: 自定义错误消息
            error_code: 错误代码
            
        Returns:
            操作结果
            
        Raises:
            SystemException: 当操作失败时
        """
        try:
            return await operation()
        except APIException:
            # 重新抛出API异常，不做处理
            raise
        except Exception as e:
            Logger.error(f"操作执行失败: {str(e)}")
            raise SystemException(
                message=error_message,
                error_code=error_code or "OPERATION_ERROR"
            )
    
    def log_operation(
        self, 
        operation: str, 
        user_id: Optional[int] = None,
        resource_id: Optional[Any] = None,
        details: Optional[dict] = None
    ) -> None:
        """记录操作日志
        
        Args:
            operation: 操作名称
            user_id: 用户ID
            resource_id: 资源ID
            details: 操作详情
        """
        log_data = {
            "operation": operation,
            "user_id": user_id,
            "resource_id": resource_id,
            "details": details or {}
        }
        Logger.info(f"服务操作: {operation}", **log_data)


class ConfigServiceMixin:
    """配置服务混入类，提供配置相关的通用功能"""
    
    def validate_config_key(self, key: str) -> None:
        """验证配置键名
        
        Args:
            key: 配置键名
            
        Raises:
            BusinessException: 当配置键名无效时
        """
        if not key or not isinstance(key, str):
            raise BusinessException("配置键名不能为空")
        
        if len(key) > 255:
            raise BusinessException("配置键名长度不能超过255个字符")
        
        # 检查键名格式（只允许字母、数字、点、下划线、连字符）
        import re
        if not re.match(r'^[a-zA-Z0-9._-]+$', key):
            raise BusinessException("配置键名只能包含字母、数字、点、下划线和连字符")
    
    def validate_config_value(self, value: Any, max_length: int = 10000) -> None:
        """验证配置值
        
        Args:
            value: 配置值
            max_length: 最大长度限制
            
        Raises:
            BusinessException: 当配置值无效时
        """
        if value is None:
            return
        
        # 如果是字符串，检查长度
        if isinstance(value, str) and len(value) > max_length:
            raise BusinessException(f"配置值长度不能超过{max_length}个字符")
    
    def sanitize_sensitive_config(self, config_data: dict, sensitive_keys: list = None) -> dict:
        """清理敏感配置信息
        
        Args:
            config_data: 配置数据
            sensitive_keys: 敏感键名列表
            
        Returns:
            清理后的配置数据
        """
        if sensitive_keys is None:
            sensitive_keys = ['password', 'secret', 'key', 'token', 'api_key']
        
        sanitized = config_data.copy()
        for key in config_data:
            if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
                sanitized[key] = "***"
        
        return sanitized


class PaginationMixin:
    """分页混入类，提供分页相关的通用功能"""
    
    def validate_pagination_params(self, page: int, page_size: int) -> tuple[int, int]:
        """验证分页参数
        
        Args:
            page: 页码
            page_size: 每页大小
            
        Returns:
            验证后的页码和每页大小
            
        Raises:
            BusinessException: 当分页参数无效时
        """
        if page < 1:
            raise BusinessException("页码必须大于0")
        
        if page_size < 1:
            raise BusinessException("每页大小必须大于0")
        
        if page_size > 1000:
            raise BusinessException("每页大小不能超过1000")
        
        return page, page_size
    
    def calculate_offset(self, page: int, page_size: int) -> int:
        """计算数据库查询偏移量
        
        Args:
            page: 页码
            page_size: 每页大小
            
        Returns:
            偏移量
        """
        return (page - 1) * page_size
    
    def create_pagination_response(
        self, 
        items: list, 
        total: int, 
        page: int, 
        page_size: int,
        message: str = "获取列表成功"
    ) -> dict:
        """创建分页响应
        
        Args:
            items: 数据项列表
            total: 总数量
            page: 当前页码
            page_size: 每页大小
            message: 响应消息
            
        Returns:
            分页响应数据
        """
        from app.core.response import ResponseModel
        return ResponseModel.create_pagination(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            message=message
        )