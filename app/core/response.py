from typing import Any, Optional, Dict, Union
from fastapi.responses import JSONResponse
from fastapi import status

class APIResponse:
    """统一的API响应格式封装"""
    
    @staticmethod
    def success(
        data: Optional[Any] = None,
        message: str = "操作成功",
        status_code: int = status.HTTP_200_OK
    ) -> JSONResponse:
        """成功响应"""
        return JSONResponse(
            status_code=status_code,
            content={
                "success": True,
                "code": status_code,
                "message": message,
                "data": data
            }
        )
    
    @staticmethod
    def error(
        message: str,
        code: int = status.HTTP_400_BAD_REQUEST,
        data: Optional[Any] = None
    ) -> JSONResponse:
        """错误响应"""
        return JSONResponse(
            status_code=code,
            content={
                "success": False,
                "code": code,
                "message": message,
                "data": data
            }
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
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "code": status.HTTP_200_OK,
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
        )