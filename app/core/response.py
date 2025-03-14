from typing import Any, Optional, Dict, Union, Callable, TypeVar, Generic
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

class PaginationModel(BaseModel):
    """分页数据模型"""
    total: int
    page: int
    page_size: int

class PaginationResponseModel(ResponseModel[T], Generic[T]):
    """分页响应模型"""
    data: Optional[Dict[str, Any]] = {
        "items": [],
        "pagination": {
            "total": 0,
            "page": 1,
            "page_size": 10
        }
    }

class APIResponse:
    """统一的API响应格式封装"""
    
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
        """成功响应"""
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
        """错误响应"""
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
        """分页数据响应"""
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
    """统一响应装饰器"""
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