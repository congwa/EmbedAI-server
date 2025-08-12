"""
统一的API响应格式封装

提供标准化的API响应格式，确保所有API接口返回一致的响应结构。
支持成功响应、错误响应、分页响应等多种场景。
    result = some_operation()  # 异常会被全局处理器捕获
    return success_response(data=result)
"""

from typing import Any, Optional, List, Dict, Callable, Generic, TypeVar
from functools import wraps
from fastapi import status
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict

from app.schemas.base import CustomBaseModel

T = TypeVar("T")


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
    """
    from app.core.response_utils import success_response as _success_response
    return _success_response(data, message, code)


class ResponseModel(CustomBaseModel, Generic[T]):
    """统一响应 Pydantic 模型"""
    success: bool = True
    code: int = status.HTTP_200_OK
    message: str = "操作成功"
    data: Optional[T] = None
    
    model_config = ConfigDict(
        json_encoders={
            # 可以在这里添加自定义的JSON编码器
        }
    )
    
    @classmethod
    def create_success(
        cls,
        data: Optional[T] = None,
        message: str = "操作成功",
        code: int = status.HTTP_200_OK
    ) -> Dict[str, Any]:
        """创建成功响应
        
        ⚠️ 废弃警告：此方法已废弃，请使用 success_response() 函数替代
        
        Args:
            data: 响应数据
            message: 响应消息
            code: HTTP状态码
            
        Returns:
            Dict[str, Any]: 响应数据字典
        """
        import warnings
        warnings.warn(
            "ResponseModel.create_success() 已废弃，请使用 success_response() 替代",
            DeprecationWarning,
            stacklevel=2
        )
        
        return success_response(data, message, code)
    
    @classmethod
    def create_error(
        cls,
        message: str,
        code: int = status.HTTP_400_BAD_REQUEST,
        data: Optional[Any] = None
    ) -> Dict[str, Any]:
        """创建错误响应
        
        ⚠️ 废弃警告：此方法已废弃，请抛出自定义异常替代
        
        Args:
            message: 错误消息
            code: HTTP状态码
            data: 错误数据
            
        Returns:
            Dict[str, Any]: 错误响应数据字典
        """
        import warnings
        warnings.warn(
            "ResponseModel.create_error() 已废弃，请抛出自定义异常替代",
            DeprecationWarning,
            stacklevel=2
        )
        
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
        """创建分页响应
        
        ⚠️ 废弃警告：此方法已废弃，请使用 pagination_response() 函数替代
        
        Args:
            items: 数据项列表
            total: 总数量
            page: 当前页码
            page_size: 每页大小
            message: 响应消息
            code: HTTP状态码
            
        Returns:
            Dict[str, Any]: 分页响应数据字典
        """
        import warnings
        warnings.warn(
            "ResponseModel.create_pagination() 已废弃，请使用 pagination_response() 替代",
            DeprecationWarning,
            stacklevel=2
        )
        
        from app.core.response_utils import pagination_response
        return pagination_response(items, total, page, page_size, message, code)


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
