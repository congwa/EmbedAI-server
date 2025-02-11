from fastapi import APIRouter
from .admin import auth, admin, document
from .client import client

api_router = APIRouter()

# 注册管理员路由
api_router.include_router(auth.router, prefix="/admin", tags=["admin"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(document.router, prefix="/admin", tags=["admin"])

# 注册客户端路由
api_router.include_router(client.router, prefix="/client", tags=["client"])