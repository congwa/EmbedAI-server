import time
from functools import wraps
from typing import Optional
from fastapi import Request, HTTPException
from app.services.auth import verify_sdk_auth
from app.core.response import APIResponse

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