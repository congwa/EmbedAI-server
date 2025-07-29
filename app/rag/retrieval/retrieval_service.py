"""检索服务"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.logger import Logger
from app.schemas.llm import LLMConfig
from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document as DBDocument
from app.models.document_chunk import DocumentChunk
from app.rag.models.document import Document
from app.rag.retrieval.retrieval_methods import RetrievalMethod
from app.rag.retrieval.retrieval_engine import RetrievalEngine
from app.rag.rerank.rerank_type import RerankMode
from app.rag.retrieval.query_cache import QueryCache

class RetrievalService:
    """检索服务
    
    提供知识库检索功能
    """
    
    def __init__(self, db: Session):
        """初始化检索服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        
    async def query(
        self,
        knowledge_base: KnowledgeBase,
        query: str,
        llm_config: LLMConfig,
        method: str = RetrievalMethod.SEMANTIC_SEARCH,
        top_k: int = 5,
        use_rerank: bool = False,
        rerank_mode: str = RerankMode.WEIGHTED_SCORE,
        user_id: Optional[str] = None,
        use_cache: bool = True,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """查询知识库
        
        Args:
            knowledge_base: 知识库对象
            query: 查询文本
            llm_config: LLM配置
            method: 检索方法
            top_k: 返回结果数量
            use_rerank: 是否使用重排序
            rerank_mode: 重排序模式
            user_id: 用户ID
            use_cache: 是否使用缓存
            **kwargs: 其他参数
            
        Returns:
            List[Dict[str, Any]]: 检索结果
        """
        import time
        start_time = time.time()
        
        # 记录服务调用开始
        Logger.rag_service_start(
            service="RetrievalService",
            method="query",
            kb_id=knowledge_base.id,
            user_id=int(user_id) if user_id and user_id.isdigit() else None
        )
        
        # 记录查询开始
        Logger.rag_query_start(
            kb_id=knowledge_base.id,
            query=query,
            method=method,
            params={
                "top_k": top_k,
                "use_rerank": use_rerank,
                "rerank_mode": rerank_mode,
                "use_cache": use_cache
            },
            user_id=int(user_id) if user_id and user_id.isdigit() else None
        )
        
        try:
            # 检查缓存
            cache_hit = False
            if use_cache:
                Logger.debug(f"检查查询缓存: 知识库ID {knowledge_base.id}")
                
                cached_results = await QueryCache.get_cached_result(
                    kb_id=knowledge_base.id,
                    query=query,
                    method=method,
                    top_k=top_k,
                    use_rerank=use_rerank,
                    rerank_mode=rerank_mode if use_rerank else None
                )
                
                if cached_results:
                    cache_hit = True
                    process_time = time.time() - start_time
                    
                    Logger.info(f"使用缓存的查询结果: {query[:50]}...")
                    
                    # 记录缓存命中
                    Logger.rag_performance_metrics(
                        operation="query_cache_hit",
                        duration=process_time,
                        kb_id=knowledge_base.id,
                        result_count=len(cached_results),
                        cache_hit=True
                    )
                    
                    # 记录查询完成（缓存）
                    Logger.rag_query_complete(
                        kb_id=knowledge_base.id,
                        query=query,
                        success=True,
                        duration=process_time,
                        result_count=len(cached_results)
                    )
                    
                    # 记录服务调用成功
                    Logger.rag_service_success(
                        service="RetrievalService",
                        method="query",
                        duration=process_time,
                        result_summary={
                            "result_count": len(cached_results),
                            "cache_hit": True,
                            "method": method
                        }
                    )
                    
                    return cached_results
                else:
                    Logger.debug(f"缓存未命中，执行实际检索: 知识库ID {knowledge_base.id}")
            
            # 创建检索引擎
            Logger.debug(f"创建检索引擎: 知识库ID {knowledge_base.id}, 方法: {method}")
            retrieval_engine = RetrievalEngine(self.db, llm_config)
            
            # 执行检索
            search_start_time = time.time()
            Logger.debug(f"开始执行检索: 方法={method}, top_k={top_k}, use_rerank={use_rerank}")
            
            results = await retrieval_engine.search(
                knowledge_base=knowledge_base,
                query=query,
                method=method,
                top_k=top_k,
                use_rerank=use_rerank,
                rerank_mode=rerank_mode,
                user_id=user_id,
                **kwargs
            )
            
            search_time = time.time() - search_start_time
            Logger.debug(f"检索执行完成: 耗时 {search_time:.3f}秒, 结果数量: {len(results) if results else 0}")
            
            # 格式化结果
            format_start_time = time.time()
            formatted_results = await self._format_results(results)
            format_time = time.time() - format_start_time
            
            Logger.debug(f"结果格式化完成: 耗时 {format_time:.3f}秒")
            
            # 提取结果统计信息
            result_count = len(formatted_results)
            scores = []
            for result in formatted_results:
                if isinstance(result, dict) and 'score' in result:
                    scores.append(result['score'])
            
            # 记录检索结果
            Logger.rag_retrieval_result(
                kb_id=knowledge_base.id,
                query=query,
                result_count=result_count,
                scores=scores,
                method=method
            )
            
            # 缓存结果
            if use_cache and not cache_hit:
                cache_start_time = time.time()
                Logger.debug(f"缓存查询结果: 知识库ID {knowledge_base.id}")
                
                await QueryCache.cache_result(
                    kb_id=knowledge_base.id,
                    query=query,
                    method=method,
                    top_k=top_k,
                    use_rerank=use_rerank,
                    rerank_mode=rerank_mode if use_rerank else None,
                    results=formatted_results,
                    expire=timedelta(hours=1)
                )
                
                cache_time = time.time() - cache_start_time
                Logger.debug(f"结果缓存完成: 耗时 {cache_time:.3f}秒")
            
            # 计算总处理时间
            total_time = time.time() - start_time
            
            # 记录查询完成
            Logger.rag_query_complete(
                kb_id=knowledge_base.id,
                query=query,
                success=True,
                duration=total_time,
                result_count=result_count
            )
            
            # 记录性能指标
            Logger.rag_performance_metrics(
                operation="query_retrieval",
                duration=total_time,
                kb_id=knowledge_base.id,
                result_count=result_count,
                cache_hit=cache_hit,
                search_time=search_time,
                format_time=format_time
            )
            
            # 记录服务调用成功
            Logger.rag_service_success(
                service="RetrievalService",
                method="query",
                duration=total_time,
                result_summary={
                    "result_count": result_count,
                    "avg_score": sum(scores) / len(scores) if scores else 0.0,
                    "method": method,
                    "use_rerank": use_rerank,
                    "cache_hit": cache_hit
                }
            )
            
            return formatted_results
            
        except Exception as e:
            # 计算处理时间
            total_time = time.time() - start_time
            
            import traceback
            error_info = traceback.format_exc()
            
            Logger.error(f"查询知识库失败: {str(e)}\n堆栈跟踪:\n{error_info}")
            
            # 记录查询失败
            Logger.rag_query_complete(
                kb_id=knowledge_base.id,
                query=query,
                success=False,
                duration=total_time,
                result_count=0
            )
            
            # 记录服务调用失败
            Logger.rag_service_error(
                service="RetrievalService",
                method="query",
                error=str(e),
                duration=total_time
            )
            
            return []
            
    async def _format_results(self, results: List[Document]) -> List[Dict[str, Any]]:
        """格式化检索结果
        
        Args:
            results: 检索结果
            
        Returns:
            List[Dict[str, Any]]: 格式化后的检索结果
        """
        try:
            Logger.debug(f"开始格式化检索结果: {len(results)} 个结果")
            formatted_results = []
            
            for i, doc in enumerate(results):
                # 获取文档ID
                document_id = doc.metadata.get("document_id")
                chunk_id = doc.metadata.get("chunk_id")
                
                # 获取文档和分块信息
                document = None
                chunk = None
                
                if document_id:
                    document = (await self.db.execute(
                        f"SELECT * FROM documents WHERE id = {document_id}"
                    )).fetchone()
                    
                if chunk_id:
                    chunk = (await self.db.execute(
                        f"SELECT * FROM document_chunks WHERE id = {chunk_id}"
                    )).fetchone()
                    
                # 构建结果
                result = {
                    "content": doc.page_content,
                    "score": doc.metadata.get("score", 0.0),
                    "metadata": doc.metadata
                }
                
                if document:
                    result["document"] = {
                        "id": document.id,
                        "title": document.title,
                        "source_url": document.source_url
                    }
                    
                if chunk:
                    result["chunk"] = {
                        "id": chunk.id,
                        "index": chunk.chunk_index
                    }
                    
                formatted_results.append(result)
                
            Logger.debug(f"检索结果格式化完成: {len(formatted_results)} 个结果")
            return formatted_results
            
        except Exception as e:
            Logger.error(f"格式化检索结果失败: {str(e)}")
            
            # 记录格式化错误的详细信息
            Logger.debug(f"格式化失败，使用简化格式: 原始结果数量 {len(results)}")
            
            # 返回简化格式的结果
            simplified_results = []
            for doc in results:
                try:
                    simplified_results.append({
                        "content": doc.page_content,
                        "score": doc.metadata.get("score", 0.0),
                        "metadata": doc.metadata
                    })
                except Exception as format_error:
                    Logger.warning(f"单个结果格式化失败: {str(format_error)}")
                    simplified_results.append({
                        "content": str(doc),
                        "score": 0.0,
                        "metadata": {}
                    })
            
            return simplified_results