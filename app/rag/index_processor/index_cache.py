"""索引缓存"""
import hashlib
import json
from typing import List, Dict, Any, Optional
from datetime import timedelta

from app.core.logger import Logger
from app.core.redis_manager import redis_manager

class IndexCache:
    """索引缓存
    
    缓存索引数据，避免重复计算
    """
    
    @staticmethod
    def _generate_cache_key(
        kb_id: int,
        index_type: str,
        document_id: Optional[int] = None
    ) -> str:
        """生成缓存键
        
        Args:
            kb_id: 知识库ID
            index_type: 索引类型
            document_id: 文档ID
            
        Returns:
            str: 缓存键
        """
        # 构建缓存键
        if document_id:
            return f"index:kb_{kb_id}:{index_type}:doc_{document_id}"
        else:
            return f"index:kb_{kb_id}:{index_type}"
    
    @staticmethod
    async def get_cached_index(
        kb_id: int,
        index_type: str,
        document_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """获取缓存的索引数据
        
        Args:
            kb_id: 知识库ID
            index_type: 索引类型
            document_id: 文档ID
            
        Returns:
            Optional[Dict[str, Any]]: 缓存的索引数据，如果没有则返回None
        """
        try:
            # 生成缓存键
            cache_key = IndexCache._generate_cache_key(kb_id, index_type, document_id)
            
            # 尝试从缓存获取
            cached = await redis_manager.get(cache_key)
            if cached:
                return json.loads(cached)
                
            return None
            
        except Exception as e:
            Logger.error(f"获取缓存索引数据失败: {str(e)}")
            return None
    
    @staticmethod
    async def cache_index(
        kb_id: int,
        index_type: str,
        index_data: Dict[str, Any],
        document_id: Optional[int] = None,
        expire: timedelta = timedelta(days=7)
    ) -> None:
        """缓存索引数据
        
        Args:
            kb_id: 知识库ID
            index_type: 索引类型
            index_data: 索引数据
            document_id: 文档ID
            expire: 过期时间
        """
        try:
            # 生成缓存键
            cache_key = IndexCache._generate_cache_key(kb_id, index_type, document_id)
            
            # 缓存结果
            await redis_manager.set(
                cache_key,
                json.dumps(index_data),
                expire=expire
            )
            
        except Exception as e:
            Logger.error(f"缓存索引数据失败: {str(e)}")
    
    @staticmethod
    async def invalidate_index(
        kb_id: int,
        index_type: str,
        document_id: Optional[int] = None
    ) -> None:
        """使索引缓存失效
        
        Args:
            kb_id: 知识库ID
            index_type: 索引类型
            document_id: 文档ID
        """
        try:
            # 生成缓存键
            cache_key = IndexCache._generate_cache_key(kb_id, index_type, document_id)
            
            # 删除缓存
            await redis_manager.delete(cache_key)
            
        except Exception as e:
            Logger.error(f"使索引缓存失效失败: {str(e)}")
    
    @staticmethod
    async def invalidate_all_indexes(kb_id: int) -> None:
        """使知识库的所有索引缓存失效
        
        Args:
            kb_id: 知识库ID
        """
        try:
            # 生成缓存键模式
            pattern = f"index:kb_{kb_id}:*"
            
            # 获取所有匹配的键
            keys = await redis_manager.keys(pattern)
            
            # 删除所有匹配的键
            if keys:
                await redis_manager.delete(*keys)
                
        except Exception as e:
            Logger.error(f"使知识库的所有索引缓存失效失败: {str(e)}")