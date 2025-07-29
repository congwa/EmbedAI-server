"""向量化引擎"""
from typing import List, Dict, Any, Optional
import numpy as np
import time

from app.core.logger import Logger
from app.schemas.llm import LLMConfig
from app.rag.embedding.cached_embedding import CacheEmbedding
from app.rag.models.document import Document

class EmbeddingEngine:
    """向量化引擎
    
    负责将文本转换为向量表示
    """
    
    def __init__(self, llm_config: LLMConfig):
        """初始化向量化引擎
        
        Args:
            llm_config: LLM配置
        """
        self.llm_config = llm_config
        self.embedding_service = CacheEmbedding(llm_config)
        
        # 记录向量化引擎初始化
        Logger.debug(f"初始化向量化引擎:")
        Logger.debug(f"  - 模型: {llm_config.embeddings.model}")
        Logger.debug(f"  - API基础URL: {llm_config.embeddings.base_url}")
        Logger.debug(f"  - 向量维度: {llm_config.embeddings.embedding_dim}")
        
        # 记录向量化模型配置
        Logger.rag_performance_metrics(
            operation="embedding_engine_init",
            duration=0.0,
            model=llm_config.embeddings.model,
            provider="embedding_service",
            dimensions=llm_config.embeddings.embedding_dim,
            base_url=llm_config.embeddings.base_url
        )
        
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """向量化文本
        
        Args:
            texts: 文本列表
            
        Returns:
            List[List[float]]: 向量列表
        """
        start_time = time.time()
        
        # 记录向量化开始
        total_text_length = sum(len(text) for text in texts)
        avg_text_length = total_text_length / len(texts) if texts else 0
        
        Logger.debug(f"开始向量化文档: {len(texts)} 个文本")
        Logger.debug(f"  - 总文本长度: {total_text_length}")
        Logger.debug(f"  - 平均文本长度: {avg_text_length:.1f}")
        Logger.debug(f"  - 模型: {self.llm_config.embeddings.model}")
        
        try:
            # 向量化
            embeddings = await self.embedding_service.embed_documents(texts)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 计算向量质量指标
            if embeddings:
                # 向量维度
                vector_dim = len(embeddings[0]) if embeddings[0] else 0
                
                # 向量范数统计
                norms = [np.linalg.norm(embedding) for embedding in embeddings]
                avg_norm = sum(norms) / len(norms) if norms else 0
                min_norm = min(norms) if norms else 0
                max_norm = max(norms) if norms else 0
                
                # 向量相似度分析（随机采样）
                if len(embeddings) > 1:
                    import random
                    sample_size = min(10, len(embeddings))
                    sample_indices = random.sample(range(len(embeddings)), sample_size)
                    similarities = []
                    
                    for i in range(len(sample_indices)):
                        for j in range(i + 1, len(sample_indices)):
                            vec1 = np.array(embeddings[sample_indices[i]])
                            vec2 = np.array(embeddings[sample_indices[j]])
                            sim = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
                            similarities.append(sim)
                    
                    avg_similarity = sum(similarities) / len(similarities) if similarities else 0
                else:
                    avg_similarity = 0
                
                # 记录向量化成功
                Logger.debug(f"文档向量化完成:")
                Logger.debug(f"  - 向量数量: {len(embeddings)}")
                Logger.debug(f"  - 向量维度: {vector_dim}")
                Logger.debug(f"  - 平均向量范数: {avg_norm:.4f}")
                Logger.debug(f"  - 向量范数范围: [{min_norm:.4f}, {max_norm:.4f}]")
                Logger.debug(f"  - 平均相似度: {avg_similarity:.4f}")
                Logger.debug(f"  - 处理耗时: {process_time:.3f}秒")
                Logger.debug(f"  - 处理速度: {len(texts)/process_time:.1f} 文本/秒")
                
                # 记录性能指标和质量评估
                Logger.rag_performance_metrics(
                    operation="embed_documents",
                    duration=process_time,
                    text_count=len(texts),
                    total_text_length=total_text_length,
                    avg_text_length=avg_text_length,
                    vector_count=len(embeddings),
                    vector_dimension=vector_dim,
                    avg_vector_norm=avg_norm,
                    min_vector_norm=min_norm,
                    max_vector_norm=max_norm,
                    avg_similarity=avg_similarity,
                    processing_speed=len(texts)/process_time if process_time > 0 else 0,
                    model=self.llm_config.embeddings.model,
                    provider="embedding_service"
                )
            
            return embeddings
            
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            import traceback
            error_info = traceback.format_exc()
            
            Logger.error(f"向量化文档失败:")
            Logger.error(f"  - 文本数量: {len(texts)}")
            Logger.error(f"  - 总文本长度: {total_text_length}")
            Logger.error(f"  - 模型: {self.llm_config.embeddings.model}")
            Logger.error(f"  - 错误信息: {str(e)}")
            Logger.debug(f"堆栈跟踪:\n{error_info}")
            
            # 记录失败的性能指标
            Logger.rag_performance_metrics(
                operation="embed_documents_failed",
                duration=process_time,
                text_count=len(texts),
                total_text_length=total_text_length,
                avg_text_length=avg_text_length,
                model=self.llm_config.embeddings.model,
                provider="embedding_service",
                error=str(e),
                error_type=type(e).__name__
            )
            
            raise
            
    async def embed_document_objects(self, documents: List[Document]) -> List[Document]:
        """向量化文档对象
        
        Args:
            documents: 文档列表
            
        Returns:
            List[Document]: 向量化后的文档列表
        """
        try:
            # 提取文本内容
            texts = [doc.page_content for doc in documents]
            
            # 向量化
            embeddings = await self.embed_documents(texts)
            
            # 更新文档对象
            for doc, embedding in zip(documents, embeddings):
                doc.vector = embedding
                
            return documents
            
        except Exception as e:
            Logger.error(f"向量化文档对象失败: {str(e)}")
            raise
            
    async def embed_query(self, query: str) -> List[float]:
        """向量化查询
        
        Args:
            query: 查询文本
            
        Returns:
            List[float]: 查询向量
        """
        start_time = time.time()
        
        # 记录查询向量化开始
        query_preview = query[:100] + "..." if len(query) > 100 else query
        Logger.debug(f"开始向量化查询: '{query_preview}'")
        Logger.debug(f"  - 查询长度: {len(query)}")
        Logger.debug(f"  - 模型: {self.llm_config.embeddings.model}")
        
        try:
            embedding = await self.embedding_service.embed_query(query)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 计算向量质量指标
            if embedding:
                vector_norm = np.linalg.norm(embedding)
                vector_dim = len(embedding)
                
                # 记录查询向量化成功
                Logger.debug(f"查询向量化完成:")
                Logger.debug(f"  - 向量维度: {vector_dim}")
                Logger.debug(f"  - 向量范数: {vector_norm:.4f}")
                Logger.debug(f"  - 处理耗时: {process_time:.3f}秒")
                
                # 记录性能指标
                Logger.rag_performance_metrics(
                    operation="embed_query",
                    duration=process_time,
                    query_length=len(query),
                    vector_dimension=vector_dim,
                    vector_norm=vector_norm,
                    model=self.llm_config.embeddings.model,
                    provider="embedding_service"
                )
            
            return embedding
            
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            import traceback
            error_info = traceback.format_exc()
            
            Logger.error(f"向量化查询失败:")
            Logger.error(f"  - 查询: '{query_preview}'")
            Logger.error(f"  - 查询长度: {len(query)}")
            Logger.error(f"  - 模型: {self.llm_config.embeddings.model}")
            Logger.error(f"  - 错误信息: {str(e)}")
            Logger.debug(f"堆栈跟踪:\n{error_info}")
            
            # 记录失败的性能指标
            Logger.rag_performance_metrics(
                operation="embed_query_failed",
                duration=process_time,
                query_length=len(query),
                model=self.llm_config.embeddings.model,
                provider="embedding_service",
                error=str(e),
                error_type=type(e).__name__
            )
            
            raise
            
    async def batch_embed_texts(
        self, texts: List[str], batch_size: int = 100
    ) -> List[List[float]]:
        """批量向量化文本
        
        Args:
            texts: 文本列表
            batch_size: 批处理大小
            
        Returns:
            List[List[float]]: 向量列表
        """
        start_time = time.time()
        
        # 计算批次信息
        total_batches = (len(texts) + batch_size - 1) // batch_size
        total_text_length = sum(len(text) for text in texts)
        
        # 记录批量向量化开始
        Logger.info(f"开始批量向量化文本:")
        Logger.info(f"  - 总文本数: {len(texts)}")
        Logger.info(f"  - 批处理大小: {batch_size}")
        Logger.info(f"  - 总批次数: {total_batches}")
        Logger.info(f"  - 总文本长度: {total_text_length}")
        Logger.info(f"  - 模型: {self.llm_config.embeddings.model}")
        
        # 记录批处理配置
        Logger.rag_performance_metrics(
            operation="batch_embed_texts_start",
            duration=0.0,
            total_texts=len(texts),
            batch_size=batch_size,
            total_batches=total_batches,
            total_text_length=total_text_length,
            model=self.llm_config.embeddings.model,
            provider="embedding_service"
        )
        
        try:
            all_embeddings = []
            successful_batches = 0
            failed_batches = 0
            
            # 分批处理
            for batch_num in range(total_batches):
                batch_start_time = time.time()
                start_idx = batch_num * batch_size
                end_idx = min(start_idx + batch_size, len(texts))
                batch = texts[start_idx:end_idx]
                
                try:
                    # 处理当前批次
                    batch_embeddings = await self.embed_documents(batch)
                    all_embeddings.extend(batch_embeddings)
                    successful_batches += 1
                    
                    # 计算批次处理时间
                    batch_time = time.time() - batch_start_time
                    
                    # 记录批次进度
                    progress = (batch_num + 1) / total_batches * 100
                    Logger.info(f"批次 {batch_num + 1}/{total_batches} 完成 - 进度: {progress:.1f}% - 耗时: {batch_time:.2f}秒")
                    
                    # 记录批次性能指标
                    Logger.rag_performance_metrics(
                        operation="batch_embed_texts_batch",
                        duration=batch_time,
                        batch_number=batch_num + 1,
                        batch_size=len(batch),
                        batch_text_length=sum(len(text) for text in batch),
                        progress_percent=progress,
                        model=self.llm_config.embeddings.model
                    )
                    
                except Exception as batch_error:
                    failed_batches += 1
                    Logger.error(f"批次 {batch_num + 1}/{total_batches} 处理失败: {str(batch_error)}")
                    
                    # 记录批次失败
                    Logger.rag_performance_metrics(
                        operation="batch_embed_texts_batch_failed",
                        duration=time.time() - batch_start_time,
                        batch_number=batch_num + 1,
                        batch_size=len(batch),
                        error=str(batch_error),
                        error_type=type(batch_error).__name__
                    )
                    
                    # 根据策略决定是否继续或抛出异常
                    raise batch_error  # 目前策略是遇到错误就停止
            
            # 计算总处理时间
            total_time = time.time() - start_time
            
            # 记录批量向量化完成
            Logger.info(f"批量向量化完成:")
            Logger.info(f"  - 成功批次: {successful_batches}/{total_batches}")
            Logger.info(f"  - 失败批次: {failed_batches}")
            Logger.info(f"  - 总向量数: {len(all_embeddings)}")
            Logger.info(f"  - 总耗时: {total_time:.2f}秒")
            Logger.info(f"  - 平均速度: {len(texts)/total_time:.1f} 文本/秒")
            
            # 记录最终性能指标
            Logger.rag_performance_metrics(
                operation="batch_embed_texts_complete",
                duration=total_time,
                total_texts=len(texts),
                successful_batches=successful_batches,
                failed_batches=failed_batches,
                total_embeddings=len(all_embeddings),
                processing_speed=len(texts)/total_time if total_time > 0 else 0,
                batch_size=batch_size,
                model=self.llm_config.embeddings.model,
                provider="embedding_service"
            )
                
            return all_embeddings
            
        except Exception as e:
            # 计算处理时间
            total_time = time.time() - start_time
            
            import traceback
            error_info = traceback.format_exc()
            
            Logger.error(f"批量向量化文本失败:")
            Logger.error(f"  - 总文本数: {len(texts)}")
            Logger.error(f"  - 批处理大小: {batch_size}")
            Logger.error(f"  - 已处理时间: {total_time:.2f}秒")
            Logger.error(f"  - 错误信息: {str(e)}")
            Logger.debug(f"堆栈跟踪:\n{error_info}")
            
            # 记录失败的性能指标
            Logger.rag_performance_metrics(
                operation="batch_embed_texts_failed",
                duration=total_time,
                total_texts=len(texts),
                batch_size=batch_size,
                total_batches=total_batches,
                model=self.llm_config.embeddings.model,
                provider="embedding_service",
                error=str(e),
                error_type=type(e).__name__
            )
            
            raise
            
    async def batch_embed_documents(
        self, documents: List[Document], batch_size: int = 100
    ) -> List[Document]:
        """批量向量化文档
        
        Args:
            documents: 文档列表
            batch_size: 批处理大小
            
        Returns:
            List[Document]: 向量化后的文档列表
        """
        try:
            # 提取文本内容
            texts = [doc.page_content for doc in documents]
            
            # 批量向量化
            embeddings = await self.batch_embed_texts(texts, batch_size)
            
            # 更新文档对象
            for doc, embedding in zip(documents, embeddings):
                doc.vector = embedding
                
            return documents
            
        except Exception as e:
            Logger.error(f"批量向量化文档失败: {str(e)}")
            raise
            
    async def compute_similarity(
        self, query_vector: List[float], document_vectors: List[List[float]]
    ) -> List[float]:
        """计算相似度
        
        Args:
            query_vector: 查询向量
            document_vectors: 文档向量列表
            
        Returns:
            List[float]: 相似度列表
        """
        start_time = time.time()
        
        # 记录相似度计算开始
        Logger.debug(f"开始计算向量相似度:")
        Logger.debug(f"  - 查询向量维度: {len(query_vector)}")
        Logger.debug(f"  - 文档向量数量: {len(document_vectors)}")
        Logger.debug(f"  - 文档向量维度: {len(document_vectors[0]) if document_vectors else 0}")
        
        try:
            # 转换为numpy数组
            query_array = np.array(query_vector)
            doc_arrays = np.array(document_vectors)
            
            # 计算余弦相似度
            similarities = np.dot(doc_arrays, query_array) / (
                np.linalg.norm(doc_arrays, axis=1) * np.linalg.norm(query_array)
            )
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 计算相似度统计
            similarities_list = similarities.tolist()
            if similarities_list:
                avg_similarity = sum(similarities_list) / len(similarities_list)
                max_similarity = max(similarities_list)
                min_similarity = min(similarities_list)
                
                # 相似度分布统计
                high_sim_count = sum(1 for sim in similarities_list if sim > 0.8)
                medium_sim_count = sum(1 for sim in similarities_list if 0.5 < sim <= 0.8)
                low_sim_count = sum(1 for sim in similarities_list if sim <= 0.5)
                
                # 记录相似度计算完成
                Logger.debug(f"向量相似度计算完成:")
                Logger.debug(f"  - 相似度数量: {len(similarities_list)}")
                Logger.debug(f"  - 平均相似度: {avg_similarity:.4f}")
                Logger.debug(f"  - 相似度范围: [{min_similarity:.4f}, {max_similarity:.4f}]")
                Logger.debug(f"  - 高相似度(>0.8): {high_sim_count}")
                Logger.debug(f"  - 中等相似度(0.5-0.8): {medium_sim_count}")
                Logger.debug(f"  - 低相似度(<=0.5): {low_sim_count}")
                Logger.debug(f"  - 计算耗时: {process_time:.3f}秒")
                
                # 记录性能指标
                Logger.rag_performance_metrics(
                    operation="compute_similarity",
                    duration=process_time,
                    query_vector_dim=len(query_vector),
                    document_vector_count=len(document_vectors),
                    document_vector_dim=len(document_vectors[0]) if document_vectors else 0,
                    avg_similarity=avg_similarity,
                    max_similarity=max_similarity,
                    min_similarity=min_similarity,
                    high_similarity_count=high_sim_count,
                    medium_similarity_count=medium_sim_count,
                    low_similarity_count=low_sim_count,
                    computation_speed=len(document_vectors)/process_time if process_time > 0 else 0
                )
            
            return similarities_list
            
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            import traceback
            error_info = traceback.format_exc()
            
            Logger.error(f"计算向量相似度失败:")
            Logger.error(f"  - 查询向量维度: {len(query_vector)}")
            Logger.error(f"  - 文档向量数量: {len(document_vectors)}")
            Logger.error(f"  - 错误信息: {str(e)}")
            Logger.debug(f"堆栈跟踪:\n{error_info}")
            
            # 记录失败的性能指标
            Logger.rag_performance_metrics(
                operation="compute_similarity_failed",
                duration=process_time,
                query_vector_dim=len(query_vector),
                document_vector_count=len(document_vectors),
                error=str(e),
                error_type=type(e).__name__
            )
            
            raise