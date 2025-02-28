from functools import wraps
from typing import Callable, Any
import pytest
from .test_state import TestState

def step_decorator(step_name: str):
    """测试步骤装饰器，用于管理测试步骤的执行状态"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # 获取 state 参数
            state = kwargs.get('state')
            if not state:
                for arg in args:
                    if isinstance(arg, TestState):
                        state = arg
                        break
            
            if not state:
                raise ValueError("TestState not found in arguments")
            
            # 如果步骤已完成，跳过
            if state.step_completed(step_name):
                return None
                
            try:
                result = await func(*args, **kwargs)
                state.mark_step_completed(step_name)
                return result
            except Exception as e:
                print(f"❌ {step_name}: {str(e)}")
                raise
                
        return wrapper
    return decorator 