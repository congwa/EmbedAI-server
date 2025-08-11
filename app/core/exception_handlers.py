"""
全局异常处理器系统

提供统一的异常处理机制，将各种异常转换为标准的HTTP响应格式。
支持开发环境和生产环境的不同处理策略。
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Union, Dict, Any
import traceback
import os
from datetime import datetime

from app.core.exceptions_new import BaseAPIException
from app.core.logger import Logger


def create_error_response(
    success: bool = False,
    code: int = 500,
    message: str = "Internal Server Error",
    data: Any = None,
    trace_id: str = None
) -> Dict[str, Any]:
    """创建标准错误响应格式
    
    Args:
        success: 是否成功，错误响应固定为False
        code: HTTP状态码
        message: 错误消息
        data: 额外的错误数据
        trace_id: 请求追踪ID
        
    Returns:
        Dict[str, Any]: 标准错误响应格式
    """
    response_data = {
        "success": success,
        "code": code,
        "message": message,
        "data": data
    }
    
    # 在开发环境中添加更多调试信息
    if os.getenv("ENVIRONMENT") == "development":
        response_data["timestamp"] = datetime.now().isoformat()
        if trace_id:
            response_data["trace_id"] = trace_id
    
    return response_data


async def base_api_exception_handler(request: Request, exc: BaseAPIException) -> JSONResponse:
    """处理自定义API异常
    
    这是新异常系统的核心处理器，处理所有继承自BaseAPIException的异常。
    
    Args:
        request: FastAPI请求对象
        exc: 自定义API异常实例
        
    Returns:
        JSONResponse: 标准格式的错误响应
    """
    # 获取请求追踪ID
    trace_id = request.headers.get("X-Trace-ID")
    
    # 记录异常日志
    Logger.error(
        f"API异常: {exc.detail['message']}",
        error_code=exc.detail.get('error_code'),
        path=str(request.url),
        method=request.method,
        trace_id=trace_id,
        data=exc.detail.get('data')
    )
    
    # 构造响应数据
    response_data = create_error_response(
        code=exc.status_code,
        message=exc.detail['message'],
        data=exc.detail.get('data'),
        trace_id=trace_id
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data,
        headers=exc.headers
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """处理FastAPI的HTTPException
    
    处理标准的HTTPException，保持与现有系统的兼容性。
    
    Args:
        request: FastAPI请求对象
        exc: HTTPException实例
        
    Returns:
        JSONResponse: 标准格式的错误响应
    """
    trace_id = request.headers.get("X-Trace-ID")
    
    # 记录异常日志
    Logger.error(
        f"HTTP异常: {exc.detail}",
        status_code=exc.status_code,
        path=str(request.url),
        method=request.method,
        trace_id=trace_id
    )
    
    # 处理detail字段，可能是字符串或字典
    message = exc.detail
    data = None
    
    if isinstance(exc.detail, dict):
        message = exc.detail.get('message', str(exc.detail))
        data = exc.detail.get('data')
    
    response_data = create_error_response(
        code=exc.status_code,
        message=message,
        data=data,
        trace_id=trace_id
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data,
        headers=exc.headers
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """处理请求验证异常
    
    处理Pydantic模型验证失败的异常，提供详细的验证错误信息。
    
    Args:
        request: FastAPI请求对象
        exc: 请求验证异常实例
        
    Returns:
        JSONResponse: 标准格式的验证错误响应
    """
    trace_id = request.headers.get("X-Trace-ID")
    
    # 解析验证错误
    errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(x) for x in error["loc"])
        error_msg = error["msg"]
        error_type = error["type"]
        
        errors.append({
            "field": field_path,
            "message": error_msg,
            "type": error_type,
            "input": error.get("input")
        })
    
    # 构造友好的错误消息
    if len(errors) == 1:
        message = f"字段 {errors[0]['field']} 验证失败: {errors[0]['message']}"
    else:
        message = f"数据验证失败，{len(errors)}个字段存在错误"
    
    # 记录验证异常日志
    Logger.warning(
        f"数据验证失败: {message}",
        path=str(request.url),
        method=request.method,
        trace_id=trace_id,
        validation_errors=errors
    )
    
    response_data = create_error_response(
        code=422,
        message=message,
        data={
            "validation_errors": errors,
            "error_count": len(errors)
        },
        trace_id=trace_id
    )
    
    return JSONResponse(
        status_code=422,
        content=response_data
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """处理SQLAlchemy数据库异常
    
    处理数据库相关的异常，在生产环境中隐藏敏感的数据库信息。
    
    Args:
        request: FastAPI请求对象
        exc: SQLAlchemy异常实例
        
    Returns:
        JSONResponse: 标准格式的数据库错误响应
    """
    trace_id = request.headers.get("X-Trace-ID")
    
    # 记录数据库异常日志
    Logger.error(
        f"数据库异常: {str(exc)}",
        path=str(request.url),
        method=request.method,
        trace_id=trace_id,
        exception_type=type(exc).__name__,
        traceback=traceback.format_exc()
    )
    
    # 在生产环境中隐藏敏感的数据库错误信息
    if os.getenv("ENVIRONMENT") == "production":
        message = "数据库操作失败"
        data = None
    else:
        message = f"数据库错误: {str(exc)}"
        data = {
            "exception_type": type(exc).__name__,
            "original_error": str(exc)
        }
    
    response_data = create_error_response(
        code=500,
        message=message,
        data=data,
        trace_id=trace_id
    )
    
    return JSONResponse(
        status_code=500,
        content=response_data
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """处理所有未被其他处理器捕获的异常
    
    这是最后的异常处理器，确保所有异常都能被正确处理。
    
    Args:
        request: FastAPI请求对象
        exc: 异常实例
        
    Returns:
        JSONResponse: 标准格式的通用错误响应
    """
    trace_id = request.headers.get("X-Trace-ID")
    
    # 记录未处理的异常
    Logger.error(
        f"未处理的异常: {str(exc)}",
        path=str(request.url),
        method=request.method,
        trace_id=trace_id,
        exception_type=type(exc).__name__,
        traceback=traceback.format_exc()
    )
    
    # 在生产环境中隐藏敏感的系统错误信息
    if os.getenv("ENVIRONMENT") == "production":
        message = "系统内部错误"
        data = None
    else:
        message = f"系统异常: {str(exc)}"
        data = {
            "exception_type": type(exc).__name__,
            "original_error": str(exc),
            "traceback": traceback.format_exc().split('\n')
        }
    
    response_data = create_error_response(
        code=500,
        message=message,
        data=data,
        trace_id=trace_id
    )
    
    return JSONResponse(
        status_code=500,
        content=response_data
    )


def register_exception_handlers(app):
    """注册所有异常处理器到FastAPI应用
    
    按照优先级顺序注册异常处理器，确保异常能被正确捕获和处理。
    
    Args:
        app: FastAPI应用实例
    """
    # 注册自定义API异常处理器（最高优先级）
    app.add_exception_handler(BaseAPIException, base_api_exception_handler)
    
    # 注册标准HTTP异常处理器
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    
    # 注册验证异常处理器
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # 注册数据库异常处理器
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    
    # 注册通用异常处理器（最低优先级，捕获所有未处理的异常）
    app.add_exception_handler(Exception, generic_exception_handler)
    
    Logger.info("异常处理器注册完成")


# ==================== 兼容性处理器 ====================

async def legacy_api_response_handler(request: Request, exc: Exception) -> JSONResponse:
    """处理旧版APIResponse产生的异常
    
    为了保持向后兼容性，处理可能仍在使用旧版APIResponse的代码。
    这个处理器将在未来版本中移除。
    
    Args:
        request: FastAPI请求对象
        exc: 异常实例
        
    Returns:
        JSONResponse: 兼容格式的错误响应
    """
    # 这里可以添加特殊的兼容性处理逻辑
    return await generic_exception_handler(request, exc)