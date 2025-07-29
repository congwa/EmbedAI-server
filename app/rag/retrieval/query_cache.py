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
        
        Logger.debug("生成查询哈希", extra={
            "kb_id": kb_id,
            "query_length": len(query),
            "query_hash": query_hash
        })
        
        # 构建缓存键
        cache_key = f"query_result:kb_{kb_id}:{query_hash}:{method}:{top_k}"
        
        # 添加重排序信息
        if use_rerank and rerank_mode:
            cache_key += f":{rerank_mode}"
            
        Logger.debug("生成缓存键完成", extra={
            "kb_id": kb_id,
            "cache_key": cache_key,
            "key_components": {
                "kb_id": kb_id,
                "query_hash": query_hash,
                "method": method,
                "top_k": top_k,
                "use_rerank": use_rerank,
                "rerank_mode": rerank_mode
            }
        })
            
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
        import time
        start_time = time.time()
        
        Logger.debug("开始获取缓存查询结果", extra={
            "kb_id": kb_id,
            "query_length": len(query),
            "method": method,
            "top_k": top_k,
            "use_rerank": use_rerank,
            "rerank_mode": rerank_mode
        })
        
        try:
            # 生成缓存键
            cache_key = QueryCache._generate_cache_key(
                kb_id, query, method, top_k, use_rerank, rerank_mode
            )
            
            Logger.debug("生成缓存键", extra={
                "kb_id": kb_id,
                "cache_key": cache_key,
                "key_length": len(cache_key)
            })
            
            # 尝试从缓存获取
            cached = await redis_manager.get(cache_key)
            
            cache_duration = time.time() - start_time
            
            if cached:
                try:
                    result = json.loads(cached)
                    result_count = len(result) if isinstance(result, list) else 0
                    
                    Logger.info("缓存命中", extra={
                        "kb_id": kb_id,
                        "cache_key": cache_key,
                        "result_count": result_count,
                        "cache_duration": cache_duration,
                        "cached_data_size": len(cached)
                    })
                    
                    # 记录缓存性能指标
                    Logger.rag_performance_metrics(
                        operation="query_cache_hit",
                        duration=cache_duration,
                        kb_id=kb_id,
                        method=method,
                        use_rerank=use_rerank,
                        result_count=result_count,
                        data_size=len(cached)
                    )
                    
                    return result
                    
                except json.JSONDecodeError as e:
                    Logger.error("缓存数据解析失败", extra={
                        "kb_id": kb_id,
                        "cache_key": cache_key,
                        "error": str(e),
                        "cached_data_preview": cached[:100] if cached else ""
                    })
                    return None
            else:
                Logger.info("缓存未命中", extra={
                    "kb_id": kb_id,
                    "cache_key": cache_key,
                    "cache_duration": cache_duration
                })
                
                # 记录缓存未命中指标
                Logger.rag_performance_metrics(
                    operation="query_cache_miss",
                    duration=cache_duration,
                    kb_id=kb_id,
                    method=method,
                    use_rerank=use_rerank
                )
                
                return None
            
        except Exception as e:
            cache_duration = time.time() - start_time
            Logger.error(f"获取缓存查询结果失败: {str(e)}", extra={
                "kb_id": kb_id,
                "method": method,
                "cache_duration": cache_duration,
                "error_type": type(e).__name__
            })
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
        import time
        start_time = time.time()
        
        Logger.debug("开始缓存查询结果", extra={
            "kb_id": kb_id,
            "query_length": len(query),
            "method": method,
            "top_k": top_k,
            "use_rerank": use_rerank,
            "rerank_mode": rerank_mode,
            "result_count": len(results),
            "expire_hours": expire.total_seconds() / 3600
        })
        
        try:
            # 生成缓存键
            cache_key = QueryCache._generate_cache_key(
                kb_id, query, method, top_k, use_rerank, rerank_mode
            )
            
            # 序列化结果
            serialized_results = json.dumps(results)
            data_size = len(serialized_results)
            
            Logger.debug("序列化查询结果", extra={
                "kb_id": kb_id,
                "cache_key": cache_key,
                "result_count": len(results),
                "serialized_size": data_size
            })
            
            # 缓存结果
            await redis_manager.set(
                cache_key,
                serialized_results,
                expire=expire
            )
            
            cache_duration = time.time() - start_time
            
            Logger.info("查询结果缓存成功", extra={
                "kb_id": kb_id,
                "cache_key": cache_key,
                "result_count": len(results),
                "data_size": data_size,
                "cache_duration": cache_duration,
                "expire_seconds": expire.total_seconds()
            })
            
            # 记录缓存性能指标
            Logger.rag_performance_metrics(
                operation="query_cache_store",
                duration=cache_duration,
                kb_id=kb_id,
                method=method,
                use_rerank=use_rerank,
                result_count=len(results),
                data_size=data_size,
                expire_seconds=expire.total_seconds()
            )
            
        except Exception as e:
            cache_duration = time.time() - start_time
            Logger.error(f"缓存查询结果失败: {str(e)}", extra={
                "kb_id": kb_id,
                "method": method,
                "result_count": len(results),
                "cache_duration": cache_duration,
                "error_type": type(e).__name__
            })
    
    @staticmethod
    def serialize_document(doc: Document) -> Dict[str, Any]:
        """序列化文档
        
        Args:
            doc: 文档对象
            
        Returns:
            Dict[str, Any]: 序列化后的文档
        """
        serialized = {
            "page_content": doc.page_content,
            "metadata": doc.metadata,
            "score": doc.metadata.get("score", 0.0)
        }
        
        Logger.debug("序列化文档", extra={
            "content_length": len(doc.page_content),
            "metadata_keys": list(doc.metadata.keys()) if doc.metadata else [],
            "score": doc.metadata.get("score", 0.0),
            "serialized_size": len(str(serialized))
        })
        
        return serialized
    
    @staticmethod
    def serialize_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """序列化查询结果
        
        Args:
            results: 查询结果
            
        Returns:
            List[Dict[str, Any]]: 序列化后的查询结果
        """
        Logger.debug("开始序列化查询结果", extra={
            "result_count": len(results)
        })
        
        serialized = []
        total_content_length = 0
        
        for i, result in enumerate(results):
            serialized_result = {
                "content": result.get("content", ""),
                "score": result.get("score", 0.0),
                "metadata": result.get("metadata", {})
            }
            
            content_length = len(serialized_result["content"])
            total_content_length += content_length
            
            if "document" in result:
                serialized_result["document"] = result["document"]
                
            if "chunk" in result:
                serialized_result["chunk"] = result["chunk"]
                
            serialized.append(serialized_result)
        
        Logger.debug("查询结果序列化完成", extra={
            "result_count": len(results),
            "serialized_count": len(serialized),
            "total_content_length": total_content_length,
            "avg_content_length": total_content_length / len(results) if results else 0,
            "avg_score": sum(r.get("score", 0) for r in results) / len(results) if results else 0
        })
            
        return serialized