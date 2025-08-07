"""管理端API包"""
from fastapi import APIRouter

# 导入子模块路由
from .admin import router as admin_router  # 管理员账户管理
from .auth import router as auth_router    # 认证相关
from .knowledge_base import router as kb_router  # 知识库管理
from .document import router as document_router  # 文档管理
from .analytics import router as analytics_router  # 分析统计
from .health import router as health_router  # 健康监控
from .rbac import router as rbac_router  # 角色权限管理
from .config import router as config_router  # 系统配置管理
from .security import router as security_router  # 安全管理
from .content import router as content_router  # 内容管理
from .integration import router as integration_router  # 集成管理
from .prompts import router as prompts_router  # 提示词管理

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

# 分析统计
router.include_router(analytics_router, prefix="/analytics", tags=["admin-analytics"])

# 健康监控
router.include_router(health_router, prefix="/health", tags=["admin-health"])

# 角色权限管理
router.include_router(rbac_router, prefix="/rbac", tags=["admin-rbac"])

# 系统配置管理
router.include_router(config_router, prefix="/config", tags=["admin-config"])

# 安全管理
router.include_router(security_router, prefix="/security", tags=["admin-security"])

# 内容管理
router.include_router(content_router, prefix="/content", tags=["admin-content"])

# 集成管理
router.include_router(integration_router, prefix="/integration", tags=["admin-integration"])

# 提示词管理
router.include_router(prompts_router, prefix="/prompts", tags=["admin-prompts"])