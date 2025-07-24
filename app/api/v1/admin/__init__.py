"""管理端API包"""
from fastapi import APIRouter

# 导入子模块路由
from .admin import router as admin_router  # 管理员账户管理
from .auth import router as auth_router    # 认证相关
from .knowledge_base import router as kb_router  # 知识库管理
from .document import router as document_router  # 文档管理

# 创建管理端总路由
router = APIRouter()

# 管理员账户管理
router.include_router(admin_router, prefix="/users", tags=["admin-users"])

# 认证相关
router.include_router(auth_router, prefix="/auth", tags=["admin-auth"])

# 知识库管理
router.include_router(kb_router, prefix="/knowledge-bases", tags=["admin-kb"])

# 文档管理
router.include_router(document_router, prefix="/documents", tags=["admin-docs"])