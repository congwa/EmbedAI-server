from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from typing import Union, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
from app.core.response import APIResponse

class BaseAPIException(HTTPException):
    def __init__(
        self,
        status_code: int,
        message: Union[str, Dict[str, Any]],
        headers: Dict[str, str] = None
    ):
        super().__init__(status_code=status_code, detail=message, headers=headers)

class DatabaseError(BaseAPIException):
    def __init__(self, message: str = "Database error occurred"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message
        )

class NotFoundError(BaseAPIException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message
        )

class ValidationError(BaseAPIException):
    def __init__(self, message: str = "Validation error"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message
        )

class AuthenticationError(BaseAPIException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            headers={"WWW-Authenticate": "Bearer"}
        )

class AuthorizationError(BaseAPIException):
    def __init__(self, message: str = "Not enough privileges"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message
        )

async def http_exception_handler(request: Request, exc: HTTPException):
    return APIResponse.error(
        message=exc.detail,
        code=exc.status_code
    )

async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    return APIResponse.error(
        message="Database error occurred",
        code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

async def validation_exception_handler(request: Request, exc: ValidationError):
    return APIResponse.error(
        message=exc.detail,
        code=exc.status_code
    )

async def generic_exception_handler(request: Request, exc: Exception):
    return APIResponse.error(
        message="An unexpected error occurred",
        code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )