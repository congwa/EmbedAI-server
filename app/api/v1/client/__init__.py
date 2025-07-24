"""客户端API包"""
from fastapi import APIRouter

# 导入子模块路由
from .knowledge_base import router as kb_router

# 创建客户端总路由
router = APIRouter()

# 添加知识库相关路由
router.include_router(kb_router, prefix="/knowledge-base", tags=["client-kb"])