from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from typing import Union, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
from app.core.response import APIResponse
from fastapi.exceptions import RequestValidationError

class BaseAPIException(HTTPException):
    """基础API异常类

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
        headers: Dict[str, str] = None
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message
        )

class NotFoundError(BaseAPIException):
    """资源未找到异常

    当请求的资源不存在时抛出此异常

    Args:
        message (str, optional): 错误信息，默认为'Resource not found'
    """
    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message
        )

class ValidationError(BaseAPIException):
    """数据验证错误异常

    当请求数据验证失败时抛出此异常

    Args:
        message (str, optional): 错误信息，默认为'Validation error'
    """
    def __init__(self, message: str = "Validation error"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message
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
            headers={"WWW-Authenticate": "Bearer"}
        )

class AuthorizationError(BaseAPIException):
    """授权错误异常

    当用户没有足够权限时抛出此异常

    Args:
        message (str, optional): 错误信息，默认为'Not enough privileges'
    """
    def __init__(self, message: str = "Not enough privileges"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message
        )

async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器

    处理所有HTTP异常，返回统一格式的错误响应

    Args:
        request (Request): FastAPI请求对象
        exc (HTTPException): HTTP异常实例

    Returns:
        APIResponse: 统一格式的错误响应
    """
    print(f"HTTP Exception occurred: {exc.detail}")  # 打印错误详情
    print(f"Status code: {exc.status_code}")  # 打印状态码
    print(f"Headers: {exc.headers}")  # 打印头信息
    return APIResponse.error(
        message=exc.detail,
        code=exc.status_code,
        data={
            "error_type": "HTTPException",
            "headers": exc.headers,
            "path": str(request.url)
        }
    )

async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """SQLAlchemy异常处理器"""
    error_msg = f"Database error: {str(exc)}"
    print(f"Database error occurred: {error_msg}")  # 打印数据库错误
    print(f"Error type: {type(exc)}")  # 打印错误类型
    return APIResponse.error(
        message=error_msg,
        code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        data={
            "error_type": "DatabaseError",
            "error_details": str(exc),
            "path": str(request.url)
        }
    )

async def validation_exception_handler(request: Request, exc: Union[ValidationError, RequestValidationError]):
    """验证异常处理器

    处理所有数据验证相关异常，返回统一格式的错误响应

    Args:
        request (Request): FastAPI请求对象
        exc (Union[ValidationError, RequestValidationError]): 验证异常实例

    Returns:
        APIResponse: 统一格式的错误响应
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

    return APIResponse.error(
        message=detail,
        code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        data={
            "error_type": "ValidationError",
            "path": str(request.url)
        }
    )

async def generic_exception_handler(request: Request, exc: Exception):
    """通用异常处理器

    处理所有未被其他处理器捕获的异常，返回统一格式的错误响应

    Args:
        request (Request): FastAPI请求对象
        exc (Exception): 异常实例

    Returns:
        APIResponse: 统一格式的错误响应
    """
    error_msg = f"An unexpected error occurred: {str(exc)}"
    print(error_msg)  # 打印错误信息
    print(f"Error type: {type(exc)}")  # 打印错误类型
    print(f"Error details: {exc.__dict__}")  # 打印错误详情
    return APIResponse.error(
        message=error_msg,
        code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        data={
            "error_type": str(type(exc).__name__),
            "error_details": str(exc),
            "path": str(request.url)
        }
    )