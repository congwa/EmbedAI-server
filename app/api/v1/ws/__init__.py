"""WebSocket API包"""
from fastapi import APIRouter
from .client import router as client_router
from .admin import router as admin_router

# 创建WebSocket总路由
router = APIRouter()

# 客户端聊天WebSocket路由
router.include_router(client_router, prefix="/chat", tags=["ws-client-chat"])

# 管理员聊天WebSocket路由
router.include_router(admin_router, prefix="/chat/admin", tags=["ws-admin-chat"]) 