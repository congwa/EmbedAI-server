from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from typing import Union, Dict, Any, Optional
from sqlalchemy.exc import SQLAlchemyError
from app.core.response_utils import success_response
from fastapi.exceptions import RequestValidationError
from app.core.logger import Logger

# ==================== 新的异常类体系 ====================


class APIException(Exception):
    """统一的API异常基类

    这是新的异常体系的基类，不再继承HTTPException，
    而是通过全局异常处理器来处理转换为HTTP响应。

    Args:
        code (int): HTTP状态码
        message (str): 错误信息
        data (Any, optional): 额外的错误数据
        headers (Dict[str, str], optional): 额外的响应头
    """

    def __init__(
        self,
        code: int,
        message: str,
        data: Any = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.code = code
        self.message = message
        self.data = data
        self.headers = headers
        super().__init__(message)


class BusinessException(APIException):
    """业务逻辑异常

    当业务规则验证失败时抛出此异常

    Args:
        message (str): 业务错误信息
        data (Any, optional): 额外的业务数据
    """

    def __init__(self, message: str, data: Any = None):
        super().__init__(code=status.HTTP_400_BAD_REQUEST, message=message, data=data)


class ResourceNotFoundException(APIException):
    """资源未找到异常

    当请求的资源不存在时抛出此异常

    Args:
        resource (str, optional): 资源名称，默认为"资源"
        resource_id (Any, optional): 资源ID
    """

    def __init__(self, resource: str = "资源", resource_id: Any = None):
        message = f"{resource}不存在"
        if resource_id:
            message += f"（ID: {resource_id}）"

        super().__init__(
            code=status.HTTP_404_NOT_FOUND,
            message=message,
            data={"resource": resource, "resource_id": resource_id},
        )


class PermissionDeniedException(APIException):
    """权限不足异常

    当用户没有足够权限执行操作时抛出此异常

    Args:
        message (str, optional): 权限错误信息
        required_permission (str, optional): 需要的权限
    """

    def __init__(self, message: str = "权限不足", required_permission: str = None):
        super().__init__(
            code=status.HTTP_403_FORBIDDEN,
            message=message,
            data={"required_permission": required_permission},
        )


class ValidationException(APIException):
    """数据验证异常

    当请求数据验证失败时抛出此异常

    Args:
        message (str): 验证错误信息
        field (str, optional): 验证失败的字段
        value (Any, optional): 验证失败的值
    """

    def __init__(self, message: str, field: str = None, value: Any = None):
        super().__init__(
            code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
            data={"field": field, "value": value},
        )


class SystemException(APIException):
    """系统异常

    当系统内部错误时抛出此异常

    Args:
        message (str, optional): 系统错误信息
        error_code (str, optional): 内部错误代码
    """

    def __init__(self, message: str = "系统内部错误", error_code: str = None):
        super().__init__(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            data={"error_code": error_code},
        )


class ConfigurationException(APIException):
    """配置异常

    当配置相关操作失败时抛出此异常

    Args:
        message (str): 配置错误信息
        config_key (str, optional): 配置键名
    """

    def __init__(self, message: str, config_key: str = None):
        super().__init__(
            code=status.HTTP_400_BAD_REQUEST,
            message=message,
            data={"config_key": config_key},
        )


# ==================== 兼容性保持 ====================


class BaseAPIException(HTTPException):
    """基础API异常类（保持向后兼容）

    所有自定义API异常的基类，继承自FastAPI的HTTPException

    Args:
        status_code (int): HTTP状态码
        message (Union[str, Dict[str, Any]]): 错误信息
        headers (Dict[str, str], optional): 额外的响应头
    """

    def __init__(
        self,
        status_code: int,
        message: Union[str, Dict[str, Any]],
        headers: Dict[str, str] = None,
    ):
        super().__init__(status_code=status_code, detail=message, headers=headers)


class DatabaseError(BaseAPIException):
    """数据库错误异常

    当数据库操作发生错误时抛出此异常

    Args:
        message (str, optional): 错误信息，默认为'Database error occurred'
    """

    def __init__(self, message: str = "Database error occurred"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, message=message
        )


class NotFoundError(BaseAPIException):
    """资源未找到异常

    当请求的资源不存在时抛出此异常

    Args:
        message (str, optional): 错误信息，默认为'Resource not found'
    """

    def __init__(self, message: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, message=message)


class ValidationError(BaseAPIException):
    """数据验证错误异常

    当请求数据验证失败时抛出此异常

    Args:
        message (str, optional): 错误信息，默认为'Validation error'
    """

    def __init__(self, message: str = "Validation error"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, message=message
        )


class AuthenticationError(BaseAPIException):
    """认证错误异常

    当用户认证失败时抛出此异常

    Args:
        message (str, optional): 错误信息，默认为'Authentication failed'
    """

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(BaseAPIException):
    """授权错误异常

    当用户没有足够权限时抛出此异常

    Args:
        message (str, optional): 错误信息，默认为'Not enough privileges'
    """

    def __init__(self, message: str = "Not enough privileges"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, message=message)


async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器

    处理所有HTTP异常，返回统一格式的错误响应

    Args:
        request (Request): FastAPI请求对象
        exc (HTTPException): HTTP异常实例

    Returns:
        JSONResponse: 统一格式的错误响应
    """
    print(f"HTTP Exception occurred: {exc.detail}")  # 打印错误详情
    print(f"Status code: {exc.status_code}")  # 打印状态码
    print(f"Headers: {exc.headers}")  # 打印头信息
    Logger.error(f"HTTP Exception occurred: {exc.detail}")
    
    response_data = {
        "success": False,
        "code": exc.status_code,
        "message": exc.detail,
        "data": {
            "error_type": "HTTPException",
            "headers": exc.headers,
            "path": str(request.url),
        }
    }
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data,
        headers=exc.headers
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """SQLAlchemy异常处理器"""
    error_msg = f"Database error: {str(exc)}"
    print(f"Database error occurred: {error_msg}")  # 打印数据库错误
    print(f"Error type: {type(exc)}")  # 打印错误类型
    Logger.error(f"Database error occurred: {error_msg}")
    
    response_data = {
        "success": False,
        "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "message": error_msg,
        "data": {
            "error_type": "DatabaseError",
            "error_details": str(exc),
            "path": str(request.url),
        }
    }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data
    )


async def validation_exception_handler(
    request: Request, exc: Union[ValidationError, RequestValidationError]
):
    """验证异常处理器

    处理所有数据验证相关异常，返回统一格式的错误响应

    Args:
        request (Request): FastAPI请求对象
        exc (Union[ValidationError, RequestValidationError]): 验证异常实例

    Returns:
        JSONResponse: 统一格式的错误响应
    """
    if isinstance(exc, RequestValidationError):
        # 处理 FastAPI 的请求验证错误
        errors = exc.errors()
        error_messages = []
        for error in errors:
            field = " -> ".join(str(x) for x in error["loc"])
            message = error["msg"]
            error_messages.append(f"{field}: {message}")
        detail = "\n".join(error_messages)
    else:
        # 处理自定义的验证错误
        detail = exc.detail

    Logger.error(f"Validation error: {detail}")
    
    response_data = {
        "success": False,
        "code": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "message": detail,
        "data": {
            "error_type": "ValidationError", 
            "path": str(request.url)
        }
    }
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_data
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """通用异常处理器

    处理所有未被其他处理器捕获的异常，返回统一格式的错误响应

    Args:
        request (Request): FastAPI请求对象
        exc (Exception): 异常实例

    Returns:
        JSONResponse: 统一格式的错误响应
    """
    error_msg = f"An unexpected error occurred: {str(exc)}"
    print(error_msg)  # 打印错误信息
    print(f"Error type: {type(exc)}")  # 打印错误类型
    print(f"Error details: {exc.__dict__}")  # 打印错误详情
    Logger.error(f"An unexpected error occurred: {str(exc)}, details: {exc.__dict__}")
    
    response_data = {
        "success": False,
        "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "message": error_msg,
        "data": {
            "error_type": str(type(exc).__name__),
            "error_details": str(exc),
            "path": str(request.url),
        }
    }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data
    )
