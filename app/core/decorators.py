import time
from functools import wraps
from typing import Optional
from fastapi import Request, HTTPException, status
from app.services.auth import verify_sdk_auth
from app.core.response import APIResponse
from app.models.enums import PermissionType
from app.services.knowledge_base import KnowledgeBaseService

def require_sdk_auth():
    """SDK认证装饰器

    用于验证请求中的SDK认证信息，包括SDK密钥、时间戳、随机数和签名。
    遵循MVC架构，将认证逻辑与响应格式分离。
    
    Returns:
        callable: 装饰器函数
    
    Raises:
        HTTPException: 当认证失败时抛出相应的错误
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从参数中获取Request对象
            request = next(
                (arg for arg in args if isinstance(arg, Request)),
                next(
                    (arg for arg in kwargs.values() if isinstance(arg, Request)),
                    None
                )
            )
            
            if not request:
                return APIResponse.error(
                    code=500,
                    message="Request object not found"
                )

            # 验证必要的请求头
            headers = {
                'sdk_key': request.headers.get('X-SDK-Key'),
                'timestamp': request.headers.get('X-SDK-Timestamp'),
                'nonce': request.headers.get('X-SDK-Nonce'),
                'signature': request.headers.get('X-SDK-Signature')
            }
            
            # 获取请求体
            body = await request.body()
            body_str = body.decode()
            
            # 使用服务层方法进行SDK认证
            is_valid, user, error_message = await verify_sdk_auth(headers, body_str)
            
            if not is_valid:
                return APIResponse.error(
                    code=401,
                    message=error_message
                )
            
            # 将验证通过的用户信息添加到请求状态中
            request.state.current_user = user
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def admin_required(func):
    """管理员权限装饰器

    用于验证当前用户是否具有管理员权限。
    遵循MVC架构，将认证逻辑与响应格式分离。
    
    Returns:
        callable: 装饰器函数
    
    Raises:
        HTTPException: 当用户不是管理员时抛出403权限错误
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        from app.services.auth import get_current_admin_user
        
        # 获取当前用户并验证管理员权限
        current_user = await get_current_admin_user()
        
        # 将验证后的用户对象传递给被装饰的函数
        kwargs['current_user'] = current_user
        return await func(*args, **kwargs)
    
    return wrapper

def require_knowledge_base_permission(required_permission: PermissionType):
    """知识库权限检查装饰器
    
    Args:
        required_permission: 所需的权限级别
        
    Returns:
        装饰器函数
        
    Raises:
        HTTPException: 当用户没有足够权限时抛出 403 错误
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从参数中获取必要的信息
            kb_id = kwargs.get('kb_id')
            current_user = kwargs.get('current_user')
            db = kwargs.get('db')
            
            if not all([kb_id, current_user, db]):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="缺少必要的参数"
                )
                
            # 检查权限
            kb_service = KnowledgeBaseService(db)
            kb = await kb_service.get(kb_id)
            if not await kb.check_permission(kb_id, current_user.id, required_permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="没有足够的权限执行此操作"
                )
                
            return await func(*args, **kwargs)
        return wrapper
    return decorator