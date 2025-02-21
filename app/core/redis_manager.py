from typing import Optional, Any, Union, Dict, List
from datetime import datetime, timedelta
import json
import aioredis
from app.core.config import settings
from app.core.logger import Logger

class RedisManager:
    """Redis管理器
    统一管理Redis连接和操作，支持异步操作
    
    功能模块：
    1. 基础缓存操作
    2. WebSocket连接管理
    3. 速率限制
    4. 任务队列管理
    """
    _instance = None
    _redis: Optional[aioredis.Redis] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisManager, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    async def initialize(cls):
        """初始化Redis连接"""
        if not cls._redis:
            try:
                cls._redis = await aioredis.from_url(
                    f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD,
                    encoding="utf-8",
                    decode_responses=True,
                    max_connections=10
                )
                Logger.info("Redis connection initialized successfully")
            except Exception as e:
                Logger.error(f"Failed to initialize Redis connection: {str(e)}")
                raise
    
    @classmethod
    async def close(cls):
        """关闭Redis连接"""
        if cls._redis:
            await cls._redis.close()
            await cls._redis.wait_closed()
            cls._redis = None
            Logger.info("Redis connection closed")
    
    @classmethod
    async def get_redis(cls) -> aioredis.Redis:
        """获取Redis连接"""
        if not cls._redis:
            await cls.initialize()
        return cls._redis
    
    # ========== 基础缓存操作 ==========
    @classmethod
    async def get(cls, key: str) -> Optional[Any]:
        """获取缓存值"""
        redis = await cls.get_redis()
        return await redis.get(key)
    
    @classmethod
    async def set(
        cls,
        key: str,
        value: Any,
        expire: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """设置缓存值"""
        redis = await cls.get_redis()
        if isinstance(expire, timedelta):
            expire = int(expire.total_seconds())
        return await redis.set(key, value, ex=expire)
    
    @classmethod
    async def delete(cls, key: str) -> bool:
        """删除缓存值"""
        redis = await cls.get_redis()
        return bool(await redis.delete(key))
    
    @classmethod
    async def incr(
        cls,
        key: str,
        amount: int = 1,
        expire: Optional[Union[int, timedelta]] = None
    ) -> int:
        """增加计数器值"""
        redis = await cls.get_redis()
        value = await redis.incr(key, amount)
        if expire:
            if isinstance(expire, timedelta):
                expire = int(expire.total_seconds())
            await redis.expire(key, expire)
        return value
    
    # ========== WebSocket连接管理 ==========
    @classmethod
    async def store_ws_connection(
        cls,
        chat_id: int,
        client_id: str,
        connection_info: dict,
        expire: int = 3600
    ) -> bool:
        """存储WebSocket连接信息"""
        redis = await cls.get_redis()
        key = f"ws:chat:{chat_id}:client:{client_id}"
        return await redis.set(key, json.dumps(connection_info), ex=expire)
    
    @classmethod
    async def get_ws_connections(cls, chat_id: int) -> Dict[str, dict]:
        """获取聊天会话的所有连接信息"""
        redis = await cls.get_redis()
        pattern = f"ws:chat:{chat_id}:client:*"
        keys = await redis.keys(pattern)
        if not keys:
            return {}
        values = await redis.mget(keys)
        return {
            key.split(":")[-1]: json.loads(value)
            for key, value in zip(keys, values)
            if value is not None
        }
    
    @classmethod
    async def remove_ws_connection(cls, chat_id: int, client_id: str) -> bool:
        """移除WebSocket连接信息"""
        redis = await cls.get_redis()
        key = f"ws:chat:{chat_id}:client:{client_id}"
        return bool(await redis.delete(key))
    
    # ========== 聊天缓存管理 ==========
    @classmethod
    async def cache_chat(cls, chat_id: int, chat_data: dict, expire: int = 3600) -> bool:
        """缓存聊天会话信息"""
        redis = await cls.get_redis()
        key = f"chat:{chat_id}"
        return await redis.set(key, json.dumps(chat_data), ex=expire)
    
    @classmethod
    async def get_cached_chat(cls, chat_id: int) -> Optional[dict]:
        """获取缓存的聊天会话信息"""
        redis = await cls.get_redis()
        key = f"chat:{chat_id}"
        data = await redis.get(key)
        return json.loads(data) if data else None
    
    @classmethod
    async def cache_message(
        cls,
        chat_id: int,
        message_data: dict,
        expire: int = 86400
    ) -> bool:
        """缓存聊天消息
        使用有序集合存储消息，分数为时间戳
        """
        redis = await cls.get_redis()
        key = f"chat:{chat_id}:messages"
        score = datetime.timestamp(message_data["created_at"])
        
        # 添加消息到有序集合
        await redis.zadd(key, {json.dumps(message_data): score})
        # 只保留最近1000条消息
        await redis.zremrangebyrank(key, 0, -1001)
        # 设置过期时间
        await redis.expire(key, expire)
        return True
    
    @classmethod
    async def get_cached_messages(
        cls,
        chat_id: int,
        start: int = 0,
        end: int = -1
    ) -> List[dict]:
        """获取缓存的消息列表"""
        redis = await cls.get_redis()
        key = f"chat:{chat_id}:messages"
        
        # 获取指定范围的消息
        messages = await redis.zrange(
            key,
            start,
            end,
            desc=True,  # 按时间倒序
            withscores=False
        )
        
        return [json.loads(msg) for msg in messages]
    
    # ========== 速率限制 ==========
    @classmethod
    async def check_rate_limit(
        cls,
        key: str,
        max_requests: int,
        time_window: Union[int, timedelta]
    ) -> bool:
        """检查是否超过速率限制
        
        Args:
            key: 限制键（如IP、用户ID等）
            max_requests: 最大请求次数
            time_window: 时间窗口
            
        Returns:
            bool: 是否允许请求
        """
        if isinstance(time_window, timedelta):
            time_window = int(time_window.total_seconds())
            
        count = await cls.incr(key, expire=time_window)
        return count <= max_requests
    
    # ========== 任务队列管理 ==========
    @classmethod
    async def add_to_training_queue(cls, kb_id: int) -> bool:
        """添加知识库到训练队列"""
        redis = await cls.get_redis()
        key = "training_queue"
        score = datetime.now().timestamp()
        return bool(await redis.zadd(key, {str(kb_id): score}))
    
    @classmethod
    async def get_next_training_task(cls) -> Optional[int]:
        """获取下一个待训练的知识库ID"""
        redis = await cls.get_redis()
        key = "training_queue"
        result = await redis.zrange(key, 0, 0)
        if result:
            # 移除已获取的任务
            await redis.zrem(key, result[0])
            return int(result[0])
        return None
    
    @classmethod
    async def clear_training_queue(cls) -> bool:
        """清空训练队列"""
        redis = await cls.get_redis()
        key = "training_queue"
        return bool(await redis.delete(key))

# 全局Redis管理器实例
redis_manager = RedisManager() 