"""查询结果缓存"""
import hashlib
import json
from typing import List, Dict, Any, Optional
from datetime import timedelta

from app.core.logger import Logger
from app.core.redis_manager import redis_manager
from app.rag.models.document import Document

class QueryCache:
    """查询结果缓存
    
    缓存查询结果，避免重复计算
    """
    
    @staticmethod
    def _generate_cache_key(
        kb_id: int,
        query: str,
        method: str,
        top_k: int,
        use_rerank: bool,
        rerank_mode: Optional[str] = None
    ) -> str:
        """生成缓存键
        
        Args:
            kb_id: 知识库ID
            query: 查询文本
            method: 检索方法
            top_k: 返回结果数量
            use_rerank: 是否使用重排序
            rerank_mode: 重排序模式
            
        Returns:
            str: 缓存键
        """
        # 生成查询哈希
        query_hash = hashlib.md5(query.encode()).hexdigest()
        
        # 构建缓存键
        cache_key = f"query_result:kb_{kb_id}:{query_hash}:{method}:{top_k}"
        
        # 添加重排序信息
        if use_rerank and rerank_mode:
            cache_key += f":{rerank_mode}"
            
        return cache_key
    
    @staticmethod
    async def get_cached_result(
        kb_id: int,
        query: str,
        method: str,
        top_k: int,
        use_rerank: bool,
        rerank_mode: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """获取缓存的查询结果
        
        Args:
            kb_id: 知识库ID
            query: 查询文本
            method: 检索方法
            top_k: 返回结果数量
            use_rerank: 是否使用重排序
            rerank_mode: 重排序模式
            
        Returns:
            Optional[List[Dict[str, Any]]]: 缓存的查询结果，如果没有则返回None
        """
        try:
            # 生成缓存键
            cache_key = QueryCache._generate_cache_key(
                kb_id, query, method, top_k, use_rerank, rerank_mode
            )
            
            # 尝试从缓存获取
            cached = await redis_manager.get(cache_key)
            if cached:
                return json.loads(cached)
                
            return None
            
        except Exception as e:
            Logger.error(f"获取缓存查询结果失败: {str(e)}")
            return None
    
    @staticmethod
    async def cache_result(
        kb_id: int,
        query: str,
        method: str,
        top_k: int,
        use_rerank: bool,
        rerank_mode: Optional[str],
        results: List[Dict[str, Any]],
        expire: timedelta = timedelta(hours=1)
    ) -> None:
        """缓存查询结果
        
        Args:
            kb_id: 知识库ID
            query: 查询文本
            method: 检索方法
            top_k: 返回结果数量
            use_rerank: 是否使用重排序
            rerank_mode: 重排序模式
            results: 查询结果
            expire: 过期时间
        """
        try:
            # 生成缓存键
            cache_key = QueryCache._generate_cache_key(
                kb_id, query, method, top_k, use_rerank, rerank_mode
            )
            
            # 缓存结果
            await redis_manager.set(
                cache_key,
                json.dumps(results),
                expire=expire
            )
            
        except Exception as e:
            Logger.error(f"缓存查询结果失败: {str(e)}")
    
    @staticmethod
    def serialize_document(doc: Document) -> Dict[str, Any]:
        """序列化文档
        
        Args:
            doc: 文档对象
            
        Returns:
            Dict[str, Any]: 序列化后的文档
        """
        return {
            "page_content": doc.page_content,
            "metadata": doc.metadata,
            "score": doc.metadata.get("score", 0.0)
        }
    
    @staticmethod
    def serialize_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """序列化查询结果
        
        Args:
            results: 查询结果
            
        Returns:
            List[Dict[str, Any]]: 序列化后的查询结果
        """
        serialized = []
        for result in results:
            serialized_result = {
                "content": result.get("content", ""),
                "score": result.get("score", 0.0),
                "metadata": result.get("metadata", {})
            }
            
            if "document" in result:
                serialized_result["document"] = result["document"]
                
            if "chunk" in result:
                serialized_result["chunk"] = result["chunk"]
                
            serialized.append(serialized_result)
            
        return serialized