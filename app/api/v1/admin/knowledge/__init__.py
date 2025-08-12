"""
知识库API路由聚合
将所有拆分的知识库API路由组合起来
"""

from fastapi import APIRouter
from app.api.v1.admin.knowledge.core import router as core_router
from app.api.v1.admin.knowledge.training import router as training_router
from app.api.v1.admin.knowledge.query import router as query_router
from app.api.v1.admin.knowledge.members import router as members_router
from app.api.v1.admin.knowledge.prompt import router as prompt_router

# 创建主路由器
router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-base"])

# 包含所有子路由
router.include_router(core_router)
router.include_router(training_router)
router.include_router(query_router)
router.include_router(members_router)
router.include_router(prompt_router) 