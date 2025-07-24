"""API v1包"""
from fastapi import APIRouter
from .admin import router as admin_router
from .client import router as client_router
from .ws import router as ws_router
from .chat import router as chat_router

# 创建主API路由器
api_router = APIRouter()

# 管理端路由 - 所有管理相关功能
api_router.include_router(
    admin_router, 
    prefix="/admin",
    tags=["admin"]
)

# 客户端路由 - 面向第三方用户的功能
api_router.include_router(
    client_router,
    prefix="/client",
    tags=["client"]
)

# WebSocket路由 - 实时通信功能
api_router.include_router(
    ws_router,
    prefix="/ws",
    tags=["websocket"]
)

# 聊天路由 - 聊天相关功能统一入口
api_router.include_router(
    chat_router,
    prefix="/chat",
    tags=["chat"]
)