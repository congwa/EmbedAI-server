"""
现代化的API异常处理系统

基于FastAPI最佳实践，提供统一的异常处理机制。
参考示例文档中的异常模式，实现声明式的错误处理。
"""

from fastapi import HTTPException, status
from typing import Optional, Any, Dict
import traceback
from datetime import datetime


class BaseAPIException(HTTPException):
    """基础API异常类
    
    所有自定义API异常的基类，提供统一的异常接口和响应格式。
    参考示例文档中的BaseHTTPException设计。
    
    Attributes:
        error_code (str): 错误代码，用于前端识别错误类型
        description (str): 默认错误描述
        code (int): HTTP状态码
        data (Optional[dict]): 额外的错误数据
    """
    
    error_code: str = "unknown_error"
    description: str = "发生了未知错误"
    code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def __init__(
        self, 
        description: Optional[str] = None, 
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        """初始化异常
        
        Args:
            description: 自定义错误描述，如果不提供则使用类默认描述
            data: 额外的错误数据，用于提供更多上下文信息
            headers: 额外的HTTP响应头
        """
        # 使用自定义描述或类默认描述
        final_description = description or self.description
        
        # 构造详细的错误信息
        detail = {
            "error_code": self.error_code,
            "message": final_description,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        # 调用父类构造函数
        super().__init__(
            status_code=self.code,
            detail=detail,
            headers=headers
        )


# ==================== 认证和权限相关异常 ====================

class UnauthorizedError(BaseAPIException):
    """认证失败异常
    
    当用户未提供有效的认证信息时抛出此异常。
    对应HTTP 401状态码。
    """
    
    error_code = "unauthorized"
    description = "认证失败，请提供有效的认证信息"
    code = status.HTTP_401_UNAUTHORIZED
    
    def __init__(self, description: Optional[str] = None, data: Optional[Any] = None):
        headers = {"WWW-Authenticate": "Bearer"}
        super().__init__(description, data, headers)


class ForbiddenError(BaseAPIException):
    """权限不足异常
    
    当用户已认证但没有足够权限执行操作时抛出此异常。
    对应HTTP 403状态码。
    """
    
    error_code = "forbidden"
    description = "权限不足，无法执行此操作"
    code = status.HTTP_403_FORBIDDEN


class InvalidTokenError(BaseAPIException):
    """无效令牌异常
    
    当提供的认证令牌无效或已过期时抛出此异常。
    """
    
    error_code = "invalid_token"
    description = "提供的认证令牌无效或已过期"
    code = status.HTTP_401_UNAUTHORIZED
    
    def __init__(self, description: Optional[str] = None, data: Optional[Any] = None):
        headers = {"WWW-Authenticate": "Bearer"}
        super().__init__(description, data, headers)


# ==================== 资源相关异常 ====================

class ResourceNotFoundError(BaseAPIException):
    """资源未找到异常
    
    当请求的资源不存在时抛出此异常。
    对应HTTP 404状态码。
    """
    
    error_code = "resource_not_found"
    description = "请求的资源不存在"
    code = status.HTTP_404_NOT_FOUND
    
    def __init__(
        self, 
        resource_name: str = "资源", 
        resource_id: Optional[Any] = None,
        description: Optional[str] = None
    ):
        """初始化资源未找到异常
        
        Args:
            resource_name: 资源名称（如"用户"、"文档"等）
            resource_id: 资源ID
            description: 自定义描述
        """
        if not description:
            description = f"{resource_name}不存在"
            if resource_id is not None:
                description += f"（ID: {resource_id}）"
        
        data = {
            "resource_name": resource_name,
            "resource_id": resource_id
        }
        
        super().__init__(description, data)


class ResourceConflictError(BaseAPIException):
    """资源冲突异常
    
    当资源已存在或存在冲突时抛出此异常。
    对应HTTP 409状态码。
    """
    
    error_code = "resource_conflict"
    description = "资源冲突"
    code = status.HTTP_409_CONFLICT


# ==================== 数据验证相关异常 ====================

class ValidationError(BaseAPIException):
    """数据验证异常
    
    当请求数据验证失败时抛出此异常。
    对应HTTP 422状态码。
    """
    
    error_code = "validation_error"
    description = "数据验证失败"
    code = status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def __init__(
        self, 
        message: str, 
        field: Optional[str] = None, 
        value: Optional[Any] = None
    ):
        """初始化验证异常
        
        Args:
            message: 验证错误信息
            field: 验证失败的字段名
            value: 验证失败的值
        """
        data = {
            "field": field,
            "value": value
        }
        
        super().__init__(message, data)


class InvalidInputError(BaseAPIException):
    """无效输入异常
    
    当输入参数不符合要求时抛出此异常。
    """
    
    error_code = "invalid_input"
    description = "输入参数无效"
    code = status.HTTP_400_BAD_REQUEST


# ==================== 业务逻辑相关异常 ====================

class BusinessError(BaseAPIException):
    """业务逻辑异常
    
    当业务规则验证失败时抛出此异常。
    对应HTTP 400状态码。
    """
    
    error_code = "business_error"
    description = "业务逻辑错误"
    code = status.HTTP_400_BAD_REQUEST


class InsufficientResourceError(BaseAPIException):
    """资源不足异常
    
    当系统资源不足以完成操作时抛出此异常。
    例如：库存不足、配额不足等。
    """
    
    error_code = "insufficient_resource"
    description = "资源不足"
    code = status.HTTP_400_BAD_REQUEST
    
    def __init__(
        self, 
        resource_type: str,
        available: Optional[int] = None,
        required: Optional[int] = None,
        description: Optional[str] = None
    ):
        """初始化资源不足异常
        
        Args:
            resource_type: 资源类型（如"库存"、"配额"等）
            available: 可用数量
            required: 需要数量
            description: 自定义描述
        """
        if not description:
            description = f"{resource_type}不足"
            if available is not None and required is not None:
                description += f"，可用: {available}，需要: {required}"
        
        data = {
            "resource_type": resource_type,
            "available": available,
            "required": required
        }
        
        super().__init__(description, data)


class OperationNotAllowedError(BaseAPIException):
    """操作不被允许异常
    
    当操作在当前状态下不被允许时抛出此异常。
    """
    
    error_code = "operation_not_allowed"
    description = "当前状态下不允许此操作"
    code = status.HTTP_400_BAD_REQUEST


# ==================== 系统相关异常 ====================

class SystemError(BaseAPIException):
    """系统内部异常
    
    当系统内部发生错误时抛出此异常。
    对应HTTP 500状态码。
    """
    
    error_code = "system_error"
    description = "系统内部错误"
    code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def __init__(
        self, 
        description: Optional[str] = None, 
        error_code: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        """初始化系统异常
        
        Args:
            description: 错误描述
            error_code: 内部错误代码
            original_exception: 原始异常对象
        """
        data = {
            "internal_error_code": error_code,
            "original_error": str(original_exception) if original_exception else None
        }
        
        # 在开发环境中包含更多调试信息
        import os
        if os.getenv("ENVIRONMENT") == "development" and original_exception:
            data["traceback"] = traceback.format_exception(
                type(original_exception), 
                original_exception, 
                original_exception.__traceback__
            )
        
        super().__init__(description, data)


class DatabaseError(BaseAPIException):
    """数据库错误异常
    
    当数据库操作发生错误时抛出此异常。
    """
    
    error_code = "database_error"
    description = "数据库操作失败"
    code = status.HTTP_500_INTERNAL_SERVER_ERROR


class ExternalServiceError(BaseAPIException):
    """外部服务错误异常
    
    当调用外部服务失败时抛出此异常。
    """
    
    error_code = "external_service_error"
    description = "外部服务调用失败"
    code = status.HTTP_502_BAD_GATEWAY
    
    def __init__(
        self, 
        service_name: str,
        description: Optional[str] = None,
        status_code: Optional[int] = None
    ):
        """初始化外部服务异常
        
        Args:
            service_name: 服务名称
            description: 错误描述
            status_code: 外部服务返回的状态码
        """
        if not description:
            description = f"{service_name}服务调用失败"
        
        data = {
            "service_name": service_name,
            "external_status_code": status_code
        }
        
        super().__init__(description, data)


# ==================== 配置相关异常 ====================

class ConfigurationError(BaseAPIException):
    """配置错误异常
    
    当系统配置错误时抛出此异常。
    """
    
    error_code = "configuration_error"
    description = "系统配置错误"
    code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def __init__(
        self, 
        config_key: Optional[str] = None,
        description: Optional[str] = None
    ):
        """初始化配置异常
        
        Args:
            config_key: 配置键名
            description: 错误描述
        """
        if not description and config_key:
            description = f"配置项 {config_key} 错误"
        
        data = {
            "config_key": config_key
        }
        
        super().__init__(description, data)


# ==================== 速率限制异常 ====================

class RateLimitExceededError(BaseAPIException):
    """速率限制异常
    
    当请求频率超过限制时抛出此异常。
    对应HTTP 429状态码。
    """
    
    error_code = "rate_limit_exceeded"
    description = "请求频率超过限制"
    code = status.HTTP_429_TOO_MANY_REQUESTS
    
    def __init__(
        self, 
        limit: Optional[int] = None,
        window: Optional[int] = None,
        retry_after: Optional[int] = None
    ):
        """初始化速率限制异常
        
        Args:
            limit: 限制次数
            window: 时间窗口（秒）
            retry_after: 建议重试时间（秒）
        """
        description = "请求频率超过限制"
        if limit and window:
            description += f"，限制: {limit}次/{window}秒"
        
        data = {
            "limit": limit,
            "window": window,
            "retry_after": retry_after
        }
        
        headers = {}
        if retry_after:
            headers["Retry-After"] = str(retry_after)
        
        super().__init__(description, data, headers)