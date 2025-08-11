"""
⚠️ 重要迁移通知：

此文件中的 APIResponse 类和相关方法已被标记为废弃。
请迁移到新的异常驱动响应系统：

新系统导入：
from app.core.response_utils import success_response, pagination_response
from app.core.exceptions_new import ResourceNotFoundError, BusinessError, etc.

迁移示例：

旧代码：
    try:
        result = some_operation()
        return APIResponse.success(data=result)
    except Exception as e:
        return APIResponse.error(message=str(e))

新代码：
    result = some_operation()  # 异常会被全局处理器捕获
    return success_response(data=result)

详细迁移指南请参考：.kiro/specs/api-response-system-refactor/
"""

from typing import Any, Optional, Dict, Union, Callable, TypeVar, Generic, List
from functools import wraps
from fastapi.responses import JSONResponse, Response
from fastapi import status
from pydantic import BaseModel, ConfigDict
from app.schemas.base import CustomBaseModel

T = TypeVar("T")

class ResponseModel(CustomBaseModel, Generic[T]):
    """统一响应 Pydantic 模型"""
    success: bool = True
    code: int = status.HTTP_200_OK
    message: str = "操作成功"
    data: Optional[T] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "code": 200,
                "message": "操作成功",
                "data": None
            }
        }
    )
    
    @classmethod
    def create_success(
        cls,
        data: Optional[T] = None,
        message: str = "操作成功",
        code: int = status.HTTP_200_OK
    ) -> Dict[str, Any]:
        """创建成功响应数据
        
        Args:
            data: 响应数据
            message: 响应消息
            code: HTTP状态码
            
        Returns:
            Dict[str, Any]: 符合ResponseModel格式的字典
        """
        return {
            "success": True,
            "code": code,
            "message": message,
            "data": data
        }
    
    @classmethod
    def create_error(
        cls,
        message: str,
        code: int = status.HTTP_400_BAD_REQUEST,
        data: Optional[Any] = None
    ) -> Dict[str, Any]:
        """创建错误响应数据
        
        Args:
            message: 错误消息
            code: HTTP状态码
            data: 额外的错误数据
            
        Returns:
            Dict[str, Any]: 符合ResponseModel格式的字典
        """
        return {
            "success": False,
            "code": code,
            "message": message,
            "data": data
        }
    
    @classmethod
    def create_pagination(
        cls,
        items: List[Any],
        total: int,
        page: int,
        page_size: int,
        message: str = "获取列表成功",
        code: int = status.HTTP_200_OK
    ) -> Dict[str, Any]:
        """创建分页响应数据
        
        Args:
            items: 数据项列表
            total: 总数量
            page: 当前页码
            page_size: 每页大小
            message: 响应消息
            code: HTTP状态码
            
        Returns:
            Dict[str, Any]: 符合分页响应格式的字典
        """
        return {
            "success": True,
            "code": code,
            "message": message,
            "data": {
                "items": items,
                "pagination": {
                    "total": total,
                    "page": page,
                    "page_size": page_size
                }
            }
        }

class PaginationModel(BaseModel):
    """分页数据模型"""
    total: int
    page: int
    page_size: int

class PaginationData(BaseModel, Generic[T]):
    """分页数据结构"""
    items: List[T]
    pagination: PaginationModel

class PaginationResponseModel(ResponseModel[PaginationData[T]], Generic[T]):
    """分页响应模型"""
    data: Optional[PaginationData[T]] = None

class APIResponse:
    """统一的API响应格式封装
    
    ⚠️ 废弃警告：此类已被标记为废弃，建议使用新的异常驱动响应机制：
    
    新的推荐用法：
    - 使用 success_response() 替代 APIResponse.success()
    - 使用自定义异常替代 APIResponse.error()
    - 使用 pagination_response() 替代 APIResponse.pagination()
    
    导入新的工具：
    from app.core.response_utils import success_response, pagination_response
    from app.core.exceptions_new import ResourceNotFoundError, BusinessError, etc.
    
    此类将在v2.0版本中移除，目前保留用于向后兼容。
    """
    
    @staticmethod
    def _process_data(data: Any) -> Any:
        """处理响应数据，自动转换 Pydantic 模型"""
        if isinstance(data, CustomBaseModel):
            return data.model_dump()
        elif isinstance(data, BaseModel):
            return data.model_dump(mode="json")
        elif isinstance(data, list):
            return [APIResponse._process_data(item) for item in data]
        elif isinstance(data, dict):
            return {k: APIResponse._process_data(v) for k, v in data.items()}
        return data
    
    @staticmethod
    def success(
        data: Optional[Any] = None,
        message: str = "操作成功",
        status_code: int = status.HTTP_200_OK
    ) -> JSONResponse:
        """成功响应
        
        ⚠️ 废弃警告：此方法已废弃，请使用新的响应工具替代
        
        推荐用法：
        from app.core.response_utils import success_response
        return success_response(data=data, message=message)
        """
        import warnings
        warnings.warn(
            "APIResponse.success() 已废弃，请使用 success_response() 替代",
            DeprecationWarning,
            stacklevel=2
        )
        
        response = ResponseModel(
            success=True,
            code=status_code,
            message=message,
            data=APIResponse._process_data(data)
        )
        return JSONResponse(
            status_code=status_code,
            content=response.model_dump()
        )
    
    @staticmethod
    def error(
        message: str,
        code: int = status.HTTP_400_BAD_REQUEST,
        data: Optional[Any] = None
    ) -> JSONResponse:
        """错误响应
        
        ⚠️ 废弃警告：此方法已废弃，请使用自定义异常替代
        
        推荐用法：
        from app.core.exceptions_new import BusinessError, ResourceNotFoundError
        raise BusinessError(message)  # 替代 APIResponse.error()
        """
        import warnings
        warnings.warn(
            "APIResponse.error() 已废弃，请抛出自定义异常替代",
            DeprecationWarning,
            stacklevel=2
        )
        
        response = ResponseModel(
            success=False,
            code=code,
            message=message,
            data=data
        )
        return JSONResponse(
            status_code=code,
            content=response.model_dump()
        )
    
    @staticmethod
    def pagination(
        items: list,
        total: int,
        page: int,
        page_size: int,
        message: str = "获取列表成功"
    ) -> JSONResponse:
        """分页数据响应
        
        ⚠️ 废弃警告：此方法已废弃，请使用新的分页响应工具替代
        
        推荐用法：
        from app.core.response_utils import pagination_response
        return pagination_response(items=items, total=total, page=page, page_size=page_size)
        """
        import warnings
        warnings.warn(
            "APIResponse.pagination() 已废弃，请使用 pagination_response() 替代",
            DeprecationWarning,
            stacklevel=2
        )
        
        pagination = PaginationModel(
            total=total,
            page=page,
            page_size=page_size
        )
        
        response = PaginationResponseModel(
            success=True,
            code=status.HTTP_200_OK,
            message=message,
            data={
                "items": APIResponse._process_data(items),
                "pagination": pagination.model_dump()
            }
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response.model_dump()
        )

def response_wrapper(
    success_code: int = status.HTTP_200_OK,
    success_msg: str = "操作成功",
    error_code: int = status.HTTP_400_BAD_REQUEST,
    error_msg: str = "操作失败"
):
    """统一响应装饰器
    
    ⚠️ 废弃警告：此装饰器已废弃，请移除装饰器并使用新的异常驱动机制
    
    推荐用法：
    1. 移除 @response_wrapper 装饰器
    2. 直接返回 success_response() 或抛出自定义异常
    3. 可选择使用 @auto_response 装饰器（来自 response_utils）
    """
    import warnings
    warnings.warn(
        "@response_wrapper 装饰器已废弃，请移除装饰器并使用新的异常驱动机制",
        DeprecationWarning,
        stacklevel=2
    )
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                result = await func(*args, **kwargs)
                
                # 如果返回的已经是 Response 对象，直接返回
                if isinstance(result, Response):
                    return result
                    
                # 如果返回的是 ResponseModel，转换为 JSONResponse
                if isinstance(result, ResponseModel):
                    return JSONResponse(
                        status_code=result.code,
                        content=result.model_dump()
                    )
                    
                # 如果返回的是元组 (data, message, status_code)
                if isinstance(result, tuple) and len(result) == 3:
                    data, message, status_code = result
                    return APIResponse.success(
                        data=data,
                        message=message,
                        status_code=status_code
                    )
                
                # 如果返回的是元组 (data, message)
                if isinstance(result, tuple) and len(result) == 2:
                    data, message = result
                    return APIResponse.success(
                        data=data,
                        message=message,
                        status_code=success_code
                    )
                
                # 默认成功响应
                return APIResponse.success(
                    data=result,
                    message=success_msg,
                    status_code=success_code
                )
                
            except Exception as e:
                # 异常处理
                return APIResponse.error(
                    message=str(e) or error_msg,
                    code=error_code
                )
                
        return wrapper
    return decorator