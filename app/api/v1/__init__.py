"""API v1包"""
from fastapi import APIRouter
from .admin import router as admin_router
from .client import router as client_router

api_router = APIRouter()

# 管理端路由
api_router.include_router(admin_router, prefix="/admin")

# 客户端路由
api_router.include_router(
    client_router,
    prefix="/client",
    tags=["client"]
)