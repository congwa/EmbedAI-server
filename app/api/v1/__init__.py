"""API v1包"""
from fastapi import APIRouter
from .admin import knowledge_base, auth, admin, document
from .client import router as client_router

api_router = APIRouter()

# 管理端路由
api_router.include_router(
    knowledge_base.router,
    prefix="/admin/knowledge-bases",
    tags=["admin"]
)
api_router.include_router(auth.router, prefix="/admin", tags=["admin"])
api_router.include_router(admin.router, prefix="/admin/users", tags=["admin"])
api_router.include_router(document.router, prefix="/admin/documents", tags=["admin"])

# 客户端路由
api_router.include_router(
    client_router,
    prefix="/client",
    tags=["client"]
)