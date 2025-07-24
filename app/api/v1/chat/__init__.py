"""聊天管理API包"""
from fastapi import APIRouter

# 导入子模块路由
from .admin import router as admin_router
from .client import router as client_router

# 创建聊天总路由
router = APIRouter()

# 管理员聊天功能路由
router.include_router(admin_router, prefix="/admin", tags=["chat-admin"])

# 客户端聊天功能路由
router.include_router(client_router, prefix="/client", tags=["chat-client"]) 