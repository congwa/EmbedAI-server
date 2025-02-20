from typing import Optional, Callable, Any
from datetime import timedelta
from functools import wraps
from fastapi import Request, HTTPException
from app.core.redis_manager import redis_manager

class RateLimiter:
    def __init__(
        self,
        key_prefix: str,
        max_requests: int,
        time_window: timedelta,
        key_func: Optional[Callable[[Request], str]] = None
    ):
        self.key_prefix = key_prefix
        self.max_requests = max_requests
        self.time_window = time_window
        self.key_func = key_func or self._default_key_func
    
    async def is_allowed(self, request: Request) -> bool:
        """检查请求是否允许通过"""
        key = f"{self.key_prefix}:{self.key_func(request)}"
        return await redis_manager.check_rate_limit(
            key=key,
            max_requests=self.max_requests,
            time_window=self.time_window
        )
    
    def _default_key_func(self, request: Request) -> str:
        """默认使用IP作为限制键"""
        return request.client.host
    
    @staticmethod
    def by_ip(
        max_requests: int,
        time_window: timedelta,
        prefix: str = "rate_limit:ip"
    ) -> "RateLimiter":
        """基于IP的访问限制"""
        return RateLimiter(prefix, max_requests, time_window)
    
    @staticmethod
    def by_custom(
        key_func: Callable[[Request], str],
        max_requests: int,
        time_window: timedelta,
        prefix: str = "rate_limit:custom"
    ) -> "RateLimiter":
        """自定义维度的访问限制"""
        return RateLimiter(prefix, max_requests, time_window, key_func)

def rate_limit(
    max_requests: int,
    time_window: timedelta,
    key_func: Optional[Callable[[Request], str]] = None,
    prefix: str = "rate_limit"
):
    """访问频率限制装饰器
    
    用法示例:
    @app.get("/api/query")
    @rate_limit(max_requests=100, time_window=timedelta(minutes=1))
    async def query(request: Request):
        return {"message": "success"}
    
    自定义限制维度:
    @rate_limit(
        max_requests=100,
        time_window=timedelta(minutes=1),
        key_func=lambda request: request.headers.get("X-API-Key", "")
    )
    """
    limiter = RateLimiter(prefix, max_requests, time_window, key_func)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Any:
            if not await limiter.is_allowed(request):
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests"
                )
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator