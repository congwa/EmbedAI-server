"""
知识库API桥接层
保持原有导入路径不变，内部使用拆分后的模块化API
"""

# 重新导出拆分后的API路由
from app.api.v1.admin.knowledge import router

# 保持向后兼容，原有的导入方式仍然有效
__all__ = ["router"]