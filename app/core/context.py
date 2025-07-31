from contextvars import ContextVar
from typing import Optional

# 定义上下文变量，并提供默认值
# 这些变量将在每个请求的生命周期内保持独立
current_user_id: ContextVar[Optional[int]] = ContextVar("current_user_id", default=None)
current_kb_id: ContextVar[Optional[int]] = ContextVar("current_kb_id", default=None)

def set_context(user_id: Optional[int] = None, kb_id: Optional[int] = None):
    """设置当前请求的上下文信息"""
    if user_id is not None:
        current_user_id.set(user_id)
    if kb_id is not None:
        current_kb_id.set(kb_id)

def get_context():
    """获取当前请求的上下文信息"""
    return {
        "user_id": current_user_id.get(),
        "kb_id": current_kb_id.get()
    }

def clear_context():
    """清除当前请求的上下文信息"""
    current_user_id.set(None)
    current_kb_id.set(None)