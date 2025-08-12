"""
响应包装工具函数

提供统一的成功响应包装功能，替代旧版的APIResponse方法。
确保响应格式与现有系统保持一致。
"""

from typing import Any, Optional, List, Dict, Union
from fastapi.responses import JSONResponse
from fastapi import status
from pydantic import BaseModel
from datetime import datetime
import os

from app.schemas.base import CustomBaseModel


def _process_response_data(data: Any) -> Any:
    """处理响应数据，自动转换Pydantic模型
    
    Args:
        data: 原始响应数据
        
    Returns:
        Any: 处理后的响应数据
    """
    if isinstance(data, CustomBaseModel):
        return data.model_dump()
    elif isinstance(data, BaseModel):
        return data.model_dump(mode="json")
    elif isinstance(data, list):
        return [_process_response_data(item) for item in data]
    elif isinstance(data, dict):
        return {k: _process_response_data(v) for k, v in data.items()}
    return data


def success_response(
    data: Optional[Any] = None,
    message: str = "操作成功",
    code: int = status.HTTP_200_OK
) -> Dict[str, Any]:
    """创建成功响应数据
    返回字典格式的响应数据，由路由函数直接返回。
    
    Args:
        data: 响应数据，支持Pydantic模型自动转换
        message: 响应消息
        code: HTTP状态码
        
    Returns:
        Dict[str, Any]: 标准格式的成功响应数据
        
    Example:
        >>> return success_response(data=user, message="用户创建成功")
        {
            "success": True,
            "code": 200,
            "message": "用户创建成功",
            "data": {...}
        }
    """
    response_data = {
        "success": True,
        "code": code,
        "message": message,
        "data": _process_response_data(data)
    }
    
    # 在开发环境中添加时间戳
    if os.getenv("ENVIRONMENT") == "development":
        response_data["timestamp"] = datetime.now().isoformat()
    
    return response_data


def pagination_response(
    items: List[Any],
    total: int,
    page: int,
    page_size: int,
    message: str = "获取列表成功",
    code: int = status.HTTP_200_OK
) -> Dict[str, Any]:
    """创建分页响应数据
    
    这是新的分页响应创建函数，替代APIResponse.pagination()。
    
    Args:
        items: 数据项列表
        total: 总数量
        page: 当前页码
        page_size: 每页大小
        message: 响应消息
        code: HTTP状态码
        
    Returns:
        Dict[str, Any]: 标准格式的分页响应数据
        
    Example:
        >>> return pagination_response(items=users, total=100, page=1, page_size=10)
        {
            "success": True,
            "code": 200,
            "message": "获取列表成功",
            "data": {
                "items": [...],
                "pagination": {
                    "total": 100,
                    "page": 1,
                    "page_size": 10,
                    "total_pages": 10,
                    "has_next": True,
                    "has_prev": False
                }
            }
        }
    """
    # 计算分页信息
    total_pages = (total + page_size - 1) // page_size  # 向上取整
    has_next = page < total_pages
    has_prev = page > 1
    
    response_data = {
        "success": True,
        "code": code,
        "message": message,
        "data": {
            "items": _process_response_data(items),
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev
            }
        }
    }
    
    # 在开发环境中添加时间戳
    if os.getenv("ENVIRONMENT") == "development":
        response_data["timestamp"] = datetime.now().isoformat()
    
    return response_data


def created_response(
    data: Optional[Any] = None,
    message: str = "创建成功",
    location: Optional[str] = None
) -> Dict[str, Any]:
    """创建资源创建成功响应
    
    专门用于资源创建成功的响应，使用201状态码。
    
    Args:
        data: 创建的资源数据
        message: 响应消息
        location: 资源位置URL（可选）
        
    Returns:
        Dict[str, Any]: 标准格式的创建成功响应数据
    """
    response_data = success_response(
        data=data,
        message=message,
        code=status.HTTP_201_CREATED
    )
    
    # 如果提供了location，可以在后续的JSONResponse中添加Location头
    if location:
        response_data["_location"] = location
    
    return response_data


def no_content_response(message: str = "操作成功") -> Dict[str, Any]:
    """创建无内容响应
    
    用于删除操作等不需要返回数据的场景，使用204状态码。
    
    Args:
        message: 响应消息
        
    Returns:
        Dict[str, Any]: 标准格式的无内容响应数据
    """
    return success_response(
        data=None,
        message=message,
        code=status.HTTP_204_NO_CONTENT
    )


def accepted_response(
    data: Optional[Any] = None,
    message: str = "请求已接受，正在处理",
    task_id: Optional[str] = None
) -> Dict[str, Any]:
    """创建请求已接受响应
    
    用于异步处理的场景，使用202状态码。
    
    Args:
        data: 响应数据
        message: 响应消息
        task_id: 任务ID（可选）
        
    Returns:
        Dict[str, Any]: 标准格式的请求已接受响应数据
    """
    response_data = success_response(
        data=data,
        message=message,
        code=status.HTTP_202_ACCEPTED
    )
    
    if task_id:
        if response_data["data"] is None:
            response_data["data"] = {}
        if isinstance(response_data["data"], dict):
            response_data["data"]["task_id"] = task_id
    
    return response_data


# ==================== 响应装饰器 ====================

from functools import wraps
from typing import Callable


def auto_response(
    success_message: str = "操作成功",
    success_code: int = status.HTTP_200_OK
):
    """自动响应装饰器
    
    自动将路由函数的返回值包装为标准响应格式。
    这是一个可选的装饰器，用于简化路由函数的响应处理。
    
    Args:
        success_message: 成功时的默认消息
        success_code: 成功时的默认状态码
        
    Returns:
        装饰器函数
        
    Example:
        @auto_response(success_message="用户获取成功")
        async def get_user(user_id: int):
            user = await user_service.get_user(user_id)
            if not user:
                raise ResourceNotFoundError("用户", user_id)
            return user  # 自动包装为标准响应格式
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Dict[str, Any]:
            result = await func(*args, **kwargs)
            
            # 如果返回值已经是标准响应格式，直接返回
            if isinstance(result, dict) and "success" in result:
                return result
            
            # 否则包装为标准响应格式
            return success_response(
                data=result,
                message=success_message,
                code=success_code
            )
        
        return wrapper
    return decorator


# ==================== 兼容性函数 ====================

def create_json_response(response_data: Dict[str, Any]) -> JSONResponse:
    """创建JSONResponse对象
    
    将响应数据转换为JSONResponse对象，处理特殊的响应头。
    
    Args:
        response_data: 响应数据字典
        
    Returns:
        JSONResponse: FastAPI响应对象
    """
    # 提取状态码
    status_code = response_data.get("code", 200)
    
    # 处理特殊的响应头
    headers = {}
    
    # 处理Location头（用于创建资源的响应）
    if "_location" in response_data:
        headers["Location"] = response_data.pop("_location")
    
    return JSONResponse(
        status_code=status_code,
        content=response_data,
        headers=headers if headers else None
    )


# ==================== 向后兼容的包装函数 ====================

class ResponseWrapper:
    """响应包装器类
    
    提供与旧版APIResponse相似的接口，用于渐进式迁移。
    这个类将在未来版本中移除。
    """
    
    @staticmethod
    def success(
        data: Optional[Any] = None,
        message: str = "操作成功",
        status_code: int = status.HTTP_200_OK
    ) -> JSONResponse:
        """成功响应（兼容性方法）
        
        警告：此方法用于向后兼容，建议使用success_response()替代
        """
        import warnings
        warnings.warn(
            "ResponseWrapper.success() 用于兼容性，建议使用 success_response() 替代",
            DeprecationWarning,
            stacklevel=2
        )
        
        response_data = success_response(data, message, status_code)
        return create_json_response(response_data)
    
    @staticmethod
    def error(
        message: str,
        code: int = status.HTTP_400_BAD_REQUEST,
        data: Optional[Any] = None
    ) -> JSONResponse:
        """错误响应（兼容性方法）
        
        警告：此方法用于向后兼容，建议抛出自定义异常替代
        """
        import warnings
        warnings.warn(
            "ResponseWrapper.error() 用于兼容性，建议抛出自定义异常替代",
            DeprecationWarning,
            stacklevel=2
        )
        
        response_data = {
            "success": False,
            "code": code,
            "message": message,
            "data": data
        }
        
        return JSONResponse(
            status_code=code,
            content=response_data
        )
    
    @staticmethod
    def pagination(
        items: List[Any],
        total: int,
        page: int,
        page_size: int,
        message: str = "获取列表成功"
    ) -> JSONResponse:
        """分页响应（兼容性方法）
        
        警告：此方法用于向后兼容，建议使用pagination_response()替代
        """
        import warnings
        warnings.warn(
            "ResponseWrapper.pagination() 用于兼容性，建议使用 pagination_response() 替代",
            DeprecationWarning,
            stacklevel=2
        )
        
        response_data = pagination_response(items, total, page, page_size, message)
        return create_json_response(response_data)