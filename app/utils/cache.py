from typing import Optional, Any, Union
from datetime import datetime, timedelta
import redis
from app.core.config import settings

class CacheManager:
    _instance = None
    _redis: Optional[redis.Redis] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CacheManager, cls).__new__(cls)
            cls._instance._init_redis()
        return cls._instance
    
    def _init_redis(self):
        """初始化Redis连接"""
        if not self._redis:
            self._redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True
            )
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        return self._redis.get(key)
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """设置缓存值"""
        if isinstance(expire, timedelta):
            expire = int(expire.total_seconds())
        return self._redis.set(key, value, ex=expire)
    
    async def incr(
        self,
        key: str,
        amount: int = 1,
        expire: Optional[Union[int, timedelta]] = None
    ) -> int:
        """增加计数器值"""
        pipe = self._redis.pipeline()
        value = pipe.incr(key, amount).execute()[0]
        if expire:
            if isinstance(expire, timedelta):
                expire = int(expire.total_seconds())
            pipe.expire(key, expire)
            pipe.execute()
        return value
    
    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        return bool(self._redis.delete(key))