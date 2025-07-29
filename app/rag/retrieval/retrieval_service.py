"""检索服务"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import timedelta
import time

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
        
        # 记录检索服务初始化
        Logger.debug(f"初始化检索服务:")
        Logger.debug(f"  - 数据库会话: {type(db).__name__}")
        Logger.debug(f"  - 支持的检索方法: {list(RetrievalMethod.__dict__.keys())}")
        Logger.debug(f"  - 支持的重排序模式: {list(RerankMode.__dict__.keys())}")
        
        # 记录初始化性能指标
        Logger.rag_performance_metrics(
            operation="retrieval_service_init",
            duration=0.0,
            supported_methods=len([attr for attr in dir(RetrievalMethod) if not attr.startswith('_')]),
            supported_rerank_modes=len([attr for attr in dir(RerankMode) if not attr.startswith('_')])
        )
        
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
        start_time = time.time()
        
        # 记录查询参数和配置
        query_preview = query[:100] + "..." if len(query) > 100 else query
        Logger.info(f"开始检索查询:")
        Logger.info(f"  - 知识库ID: {knowledge_base.id}")
        Logger.info(f"  - 知识库名称: {knowledge_base.name}")
        Logger.info(f"  - 查询: '{query_preview}'")
        Logger.info(f"  - 查询长度: {len(query)}")
        Logger.info(f"  - 检索方法: {method}")
        Logger.info(f"  - 返回数量: {top_k}")
        Logger.info(f"  - 使用重排序: {use_rerank}")
        Logger.info(f"  - 重排序模式: {rerank_mode if use_rerank else 'N/A'}")
        Logger.info(f"  - 使用缓存: {use_cache}")
        Logger.info(f"  - 用户ID: {user_id or 'N/A'}")
        
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
                "use_cache": use_cache,
                "query_length": len(query)
            },
            user_id=int(user_id) if user_id and user_id.isdigit() else None
        )
        
        # 记录查询配置的性能指标
        Logger.rag_performance_metrics(
            operation="retrieval_query_config",
            duration=0.0,
            kb_id=knowledge_base.id,
            kb_name=knowledge_base.name,
            query_length=len(query),
            retrieval_method=method,
            top_k=top_k,
            use_rerank=use_rerank,
            rerank_mode=rerank_mode if use_rerank else None,
            use_cache=use_cache,
            user_id=user_id
        )
        
        try:
            # 检查缓存
            cache_hit = False
            cache_check_time = 0
            
            if use_cache:
                cache_check_start = time.time()
                Logger.debug(f"开始检查查询缓存:")
                Logger.debug(f"  - 知识库ID: {knowledge_base.id}")
                Logger.debug(f"  - 查询哈希: {hash(query)}")
                Logger.debug(f"  - 检索方法: {method}")
                Logger.debug(f"  - 参数组合: top_k={top_k}, rerank={use_rerank}")
                
                cached_results = await QueryCache.get_cached_result(
                    kb_id=knowledge_base.id,
                    query=query,
                    method=method,
                    top_k=top_k,
                    use_rerank=use_rerank,
                    rerank_mode=rerank_mode if use_rerank else None
                )
                
                cache_check_time = time.time() - cache_check_start
                
                if cached_results:
                    cache_hit = True
                    process_time = time.time() - start_time
                    
                    # 计算缓存结果统计
                    cache_scores = []
                    for result in cached_results:
                        if isinstance(result, dict) and 'score' in result:
                            cache_scores.append(result['score'])
                    
                    avg_cache_score = sum(cache_scores) / len(cache_scores) if cache_scores else 0.0
                    
                    Logger.info(f"缓存命中，返回缓存结果:")
                    Logger.info(f"  - 缓存检查耗时: {cache_check_time:.3f}秒")
                    Logger.info(f"  - 缓存结果数: {len(cached_results)}")
                    Logger.info(f"  - 平均相似度: {avg_cache_score:.4f}")
                    Logger.info(f"  - 总耗时: {process_time:.3f}秒")
                    
                    # 记录缓存命中的性能指标
                    Logger.rag_performance_metrics(
                        operation="query_cache_hit",
                        duration=process_time,
                        kb_id=knowledge_base.id,
                        query_length=len(query),
                        result_count=len(cached_results),
                        avg_score=avg_cache_score,
                        cache_check_time=cache_check_time,
                        cache_hit=True,
                        retrieval_method=method,
                        top_k=top_k,
                        use_rerank=use_rerank
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
                            "avg_score": avg_cache_score,
                            "cache_hit": True,
                            "method": method,
                            "cache_check_time": cache_check_time
                        }
                    )
                    
                    return cached_results
                else:
                    Logger.debug(f"缓存未命中，执行实际检索:")
                    Logger.debug(f"  - 缓存检查耗时: {cache_check_time:.3f}秒")
                    Logger.debug(f"  - 将执行方法: {method}")
            else:
                Logger.debug(f"缓存已禁用，直接执行检索")
            
            # 创建检索引擎
            engine_start_time = time.time()
            Logger.debug(f"创建检索引擎:")
            Logger.debug(f"  - 知识库ID: {knowledge_base.id}")
            Logger.debug(f"  - 检索方法: {method}")
            Logger.debug(f"  - LLM配置: {llm_config.embeddings.model}")
            
            retrieval_engine = RetrievalEngine(self.db, llm_config)
            engine_init_time = time.time() - engine_start_time
            
            Logger.debug(f"检索引擎创建完成，耗时: {engine_init_time:.3f}秒")
            
            # 执行检索
            search_start_time = time.time()
            Logger.info(f"开始执行检索:")
            Logger.info(f"  - 检索方法: {method}")
            Logger.info(f"  - 返回数量: {top_k}")
            Logger.info(f"  - 使用重排序: {use_rerank}")
            Logger.info(f"  - 重排序模式: {rerank_mode if use_rerank else 'N/A'}")
            
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
            result_count = len(results) if results else 0
            
            Logger.info(f"检索执行完成:")
            Logger.info(f"  - 检索耗时: {search_time:.3f}秒")
            Logger.info(f"  - 结果数量: {result_count}")
            Logger.info(f"  - 检索速度: {result_count/search_time:.1f} 结果/秒" if search_time > 0 else "  - 检索速度: N/A")
            
            # 分析检索结果质量
            if results:
                result_scores = []
                result_lengths = []
                
                for doc in results:
                    if hasattr(doc, 'metadata') and isinstance(doc.metadata, dict):
                        score = doc.metadata.get('score', 0.0)
                        if isinstance(score, (int, float)):
                            result_scores.append(float(score))
                    
                    if hasattr(doc, 'page_content'):
                        result_lengths.append(len(doc.page_content))
                
                avg_score = sum(result_scores) / len(result_scores) if result_scores else 0.0
                max_score = max(result_scores) if result_scores else 0.0
                min_score = min(result_scores) if result_scores else 0.0
                avg_length = sum(result_lengths) / len(result_lengths) if result_lengths else 0.0
                
                Logger.debug(f"检索结果质量分析:")
                Logger.debug(f"  - 平均相似度: {avg_score:.4f}")
                Logger.debug(f"  - 相似度范围: [{min_score:.4f}, {max_score:.4f}]")
                Logger.debug(f"  - 平均内容长度: {avg_length:.1f}")
                Logger.debug(f"  - 有效分数数量: {len(result_scores)}/{result_count}")
            else:
                Logger.warning(f"检索未返回任何结果")
                avg_score = max_score = min_score = avg_length = 0.0
            
            # 格式化结果
            format_start_time = time.time()
            Logger.debug(f"开始格式化检索结果: {result_count} 个结果")
            
            formatted_results = await self._format_results(results)
            format_time = time.time() - format_start_time
            
            Logger.debug(f"结果格式化完成:")
            Logger.debug(f"  - 格式化耗时: {format_time:.3f}秒")
            Logger.debug(f"  - 格式化速度: {result_count/format_time:.1f} 结果/秒" if format_time > 0 else "  - 格式化速度: N/A")
            
            # 提取格式化结果的统计信息
            final_result_count = len(formatted_results)
            formatted_scores = []
            content_lengths = []
            
            for result in formatted_results:
                if isinstance(result, dict):
                    if 'score' in result:
                        formatted_scores.append(result['score'])
                    if 'content' in result:
                        content_lengths.append(len(result['content']))
            
            avg_formatted_score = sum(formatted_scores) / len(formatted_scores) if formatted_scores else 0.0
            avg_content_length = sum(content_lengths) / len(content_lengths) if content_lengths else 0.0
            
            # 记录检索结果
            Logger.rag_retrieval_result(
                kb_id=knowledge_base.id,
                query=query,
                result_count=final_result_count,
                scores=formatted_scores,
                method=method
            )
            
            # 缓存结果
            cache_store_time = 0
            if use_cache and not cache_hit and formatted_results:
                cache_start_time = time.time()
                Logger.debug(f"开始缓存查询结果:")
                Logger.debug(f"  - 知识库ID: {knowledge_base.id}")
                Logger.debug(f"  - 结果数量: {final_result_count}")
                Logger.debug(f"  - 缓存过期时间: 1小时")
                
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
                
                cache_store_time = time.time() - cache_start_time
                Logger.debug(f"结果缓存完成:")
                Logger.debug(f"  - 缓存存储耗时: {cache_store_time:.3f}秒")
                Logger.debug(f"  - 缓存存储速度: {final_result_count/cache_store_time:.1f} 结果/秒" if cache_store_time > 0 else "  - 缓存存储速度: N/A")
            elif use_cache and not cache_hit and not formatted_results:
                Logger.debug(f"跳过缓存：无结果可缓存")
            elif not use_cache:
                Logger.debug(f"跳过缓存：缓存已禁用")
            
            # 计算总处理时间
            total_time = time.time() - start_time
            
            # 记录查询完成统计
            Logger.info(f"检索查询完成:")
            Logger.info(f"  - 知识库ID: {knowledge_base.id}")
            Logger.info(f"  - 最终结果数: {final_result_count}")
            Logger.info(f"  - 平均相似度: {avg_formatted_score:.4f}")
            Logger.info(f"  - 平均内容长度: {avg_content_length:.1f}")
            Logger.info(f"  - 缓存命中: {'是' if cache_hit else '否'}")
            Logger.info(f"  - 引擎初始化耗时: {engine_init_time:.3f}秒")
            Logger.info(f"  - 检索执行耗时: {search_time:.3f}秒")
            Logger.info(f"  - 结果格式化耗时: {format_time:.3f}秒")
            Logger.info(f"  - 缓存存储耗时: {cache_store_time:.3f}秒")
            Logger.info(f"  - 总处理耗时: {total_time:.3f}秒")
            Logger.info(f"  - 整体处理速度: {final_result_count/total_time:.1f} 结果/秒" if total_time > 0 else "  - 整体处理速度: N/A")
            
            # 记录查询完成
            Logger.rag_query_complete(
                kb_id=knowledge_base.id,
                query=query,
                success=True,
                duration=total_time,
                result_count=final_result_count
            )
            
            # 记录详细的性能指标
            Logger.rag_performance_metrics(
                operation="retrieval_query_complete",
                duration=total_time,
                kb_id=knowledge_base.id,
                kb_name=knowledge_base.name,
                query_length=len(query),
                retrieval_method=method,
                top_k=top_k,
                use_rerank=use_rerank,
                rerank_mode=rerank_mode if use_rerank else None,
                use_cache=use_cache,
                cache_hit=cache_hit,
                cache_check_time=cache_check_time,
                engine_init_time=engine_init_time,
                search_time=search_time,
                format_time=format_time,
                cache_store_time=cache_store_time,
                result_count=final_result_count,
                avg_score=avg_formatted_score,
                avg_content_length=avg_content_length,
                processing_speed=final_result_count/total_time if total_time > 0 else 0,
                search_speed=result_count/search_time if search_time > 0 else 0,
                format_speed=final_result_count/format_time if format_time > 0 else 0
            )
            
            # 记录服务调用成功
            Logger.rag_service_success(
                service="RetrievalService",
                method="query",
                duration=total_time,
                result_summary={
                    "result_count": final_result_count,
                    "avg_score": avg_formatted_score,
                    "avg_content_length": avg_content_length,
                    "method": method,
                    "use_rerank": use_rerank,
                    "cache_hit": cache_hit,
                    "search_time": search_time,
                    "format_time": format_time,
                    "cache_store_time": cache_store_time,
                    "processing_speed": final_result_count/total_time if total_time > 0 else 0
                }
            )
            
            return formatted_results
            
        except Exception as e:
            # 计算处理时间
            total_time = time.time() - start_time
            
            import traceback
            error_info = traceback.format_exc()
            
            Logger.error(f"检索查询失败:")
            Logger.error(f"  - 知识库ID: {knowledge_base.id}")
            Logger.error(f"  - 查询: '{query_preview}'")
            Logger.error(f"  - 检索方法: {method}")
            Logger.error(f"  - 已处理时间: {total_time:.3f}秒")
            Logger.error(f"  - 错误类型: {type(e).__name__}")
            Logger.error(f"  - 错误信息: {str(e)}")
            Logger.debug(f"堆栈跟踪:\n{error_info}")
            
            # 记录查询失败
            Logger.rag_query_complete(
                kb_id=knowledge_base.id,
                query=query,
                success=False,
                duration=total_time,
                result_count=0
            )
            
            # 记录失败的性能指标
            Logger.rag_performance_metrics(
                operation="retrieval_query_failed",
                duration=total_time,
                kb_id=knowledge_base.id,
                kb_name=knowledge_base.name,
                query_length=len(query),
                retrieval_method=method,
                top_k=top_k,
                use_rerank=use_rerank,
                use_cache=use_cache,
                error=str(e),
                error_type=type(e).__name__
            )
            
            # 记录服务调用失败
            Logger.rag_service_error(
                service="RetrievalService",
                method="query",
                error=str(e),
                duration=total_time,
                kb_id=knowledge_base.id,
                error_type=type(e).__name__
            )
            
            return []
            
    async def _format_results(self, results: List[Document]) -> List[Dict[str, Any]]:
        """格式化检索结果
        
        Args:
            results: 检索结果
            
        Returns:
            List[Dict[str, Any]]: 格式化后的检索结果
        """
        format_start_time = time.time()
        
        try:
            Logger.debug(f"开始格式化检索结果:")
            Logger.debug(f"  - 原始结果数: {len(results)}")
            
            formatted_results = []
            db_query_count = 0
            db_query_time = 0
            format_errors = 0
            
            for i, doc in enumerate(results):
                try:
                    # 获取文档ID
                    document_id = doc.metadata.get("document_id")
                    chunk_id = doc.metadata.get("chunk_id")
                    
                    # 获取文档和分块信息
                    document = None
                    chunk = None
                    
                    if document_id:
                        db_start = time.time()
                        document = (await self.db.execute(
                            f"SELECT * FROM documents WHERE id = {document_id}"
                        )).fetchone()
                        db_query_time += time.time() - db_start
                        db_query_count += 1
                        
                    if chunk_id:
                        db_start = time.time()
                        chunk = (await self.db.execute(
                            f"SELECT * FROM document_chunks WHERE id = {chunk_id}"
                        )).fetchone()
                        db_query_time += time.time() - db_start
                        db_query_count += 1
                        
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
                    
                except Exception as item_error:
                    format_errors += 1
                    Logger.warning(f"格式化第 {i+1} 个结果失败: {str(item_error)}")
                    
                    # 使用简化格式
                    try:
                        simplified_result = {
                            "content": doc.page_content if hasattr(doc, 'page_content') else str(doc),
                            "score": doc.metadata.get("score", 0.0) if hasattr(doc, 'metadata') and isinstance(doc.metadata, dict) else 0.0,
                            "metadata": doc.metadata if hasattr(doc, 'metadata') and isinstance(doc.metadata, dict) else {}
                        }
                        formatted_results.append(simplified_result)
                    except Exception as fallback_error:
                        Logger.error(f"简化格式化也失败: {str(fallback_error)}")
                        # 最后的备用格式
                        formatted_results.append({
                            "content": "格式化失败的结果",
                            "score": 0.0,
                            "metadata": {"error": "format_failed"}
                        })
            
            # 计算格式化统计
            total_format_time = time.time() - format_start_time
            success_rate = (len(results) - format_errors) / len(results) if results else 1.0
            
            Logger.debug(f"检索结果格式化完成:")
            Logger.debug(f"  - 格式化结果数: {len(formatted_results)}")
            Logger.debug(f"  - 格式化成功率: {success_rate:.2%}")
            Logger.debug(f"  - 格式化错误数: {format_errors}")
            Logger.debug(f"  - 数据库查询次数: {db_query_count}")
            Logger.debug(f"  - 数据库查询耗时: {db_query_time:.3f}秒")
            Logger.debug(f"  - 总格式化耗时: {total_format_time:.3f}秒")
            
            # 记录格式化性能指标
            Logger.rag_performance_metrics(
                operation="format_retrieval_results",
                duration=total_format_time,
                input_count=len(results),
                output_count=len(formatted_results),
                success_rate=success_rate,
                format_errors=format_errors,
                db_query_count=db_query_count,
                db_query_time=db_query_time,
                format_speed=len(results)/total_format_time if total_format_time > 0 else 0
            )
            
            return formatted_results
            
        except Exception as e:
            # 计算处理时间
            total_format_time = time.time() - format_start_time
            
            import traceback
            error_info = traceback.format_exc()
            
            Logger.error(f"格式化检索结果失败:")
            Logger.error(f"  - 原始结果数: {len(results)}")
            Logger.error(f"  - 已处理时间: {total_format_time:.3f}秒")
            Logger.error(f"  - 错误信息: {str(e)}")
            Logger.debug(f"堆栈跟踪:\n{error_info}")
            
            # 记录格式化失败的性能指标
            Logger.rag_performance_metrics(
                operation="format_retrieval_results_failed",
                duration=total_format_time,
                input_count=len(results),
                error=str(e),
                error_type=type(e).__name__
            )
            
            # 返回简化格式的结果
            Logger.debug(f"使用简化格式作为备用方案")
            simplified_results = []
            
            for i, doc in enumerate(results):
                try:
                    simplified_results.append({
                        "content": doc.page_content if hasattr(doc, 'page_content') else str(doc),
                        "score": doc.metadata.get("score", 0.0) if hasattr(doc, 'metadata') and isinstance(doc.metadata, dict) else 0.0,
                        "metadata": doc.metadata if hasattr(doc, 'metadata') and isinstance(doc.metadata, dict) else {}
                    })
                except Exception as format_error:
                    Logger.warning(f"简化格式化第 {i+1} 个结果失败: {str(format_error)}")
                    simplified_results.append({
                        "content": "无法格式化的结果",
                        "score": 0.0,
                        "metadata": {"error": "format_failed", "index": i}
                    })
            
            Logger.debug(f"简化格式化完成: {len(simplified_results)} 个结果")
            return simplified_results