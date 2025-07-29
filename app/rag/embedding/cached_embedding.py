"""缓存向量化实现"""
import hashlib
import json
from typing import List, Optional, Dict, Any
import numpy as np
import time
from datetime import timedelta

from app.core.logger import Logger
from app.core.redis_manager import redis_manager
from app.schemas.llm import LLMConfig
from app.rag.embedding.embedding_base import Embeddings

class CacheEmbedding(Embeddings):
    """缓存向量化实现
    
    使用Redis缓存向量化结果，避免重复计算
    """
    
    def __init__(self, llm_config: LLMConfig):
        """初始化缓存向量化
        
        Args:
            llm_config: LLM配置
        """
        self.llm_config = llm_config
        self.model = llm_config.embeddings.model
        self.provider = "embedding_service"  # 默认提供商名称
        self.api_base = llm_config.embeddings.base_url
        self.api_key = llm_config.embeddings.api_key
        
        # 记录缓存向量化初始化
        Logger.debug(f"初始化缓存向量化服务:")
        Logger.debug(f"  - 模型: {self.model}")
        Logger.debug(f"  - 提供商: {self.provider}")
        Logger.debug(f"  - API基础URL: {self.api_base}")
        Logger.debug(f"  - 缓存策略: Redis缓存，文档7天，查询24小时")
        
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """向量化文档
        
        Args:
            texts: 文本列表
            
        Returns:
            List[List[float]]: 向量列表
        """
        start_time = time.time()
        
        # 记录缓存向量化开始
        Logger.debug(f"开始缓存向量化文档: {len(texts)} 个文本")
        
        # 初始化结果列表
        embeddings: List[Optional[List[float]]] = [None] * len(texts)
        
        # 需要向量化的文本索引
        embedding_indices = []
        cache_hits = 0
        cache_misses = 0
        
        # 检查缓存
        cache_check_start = time.time()
        for i, text in enumerate(texts):
            text_hash = self._generate_hash(text)
            cache_key = f"embedding:doc:{self.provider}:{self.model}:{text_hash}"
            
            # 尝试从缓存获取
            cached = await redis_manager.get(cache_key)
            if cached:
                try:
                    embeddings[i] = json.loads(cached)
                    cache_hits += 1
                except Exception as e:
                    Logger.warning(f"解析缓存向量失败: {str(e)}")
                    embedding_indices.append(i)
                    cache_misses += 1
            else:
                embedding_indices.append(i)
                cache_misses += 1
        
        cache_check_time = time.time() - cache_check_start
        cache_hit_rate = cache_hits / len(texts) if texts else 0
        
        # 记录缓存统计
        Logger.debug(f"缓存检查完成:")
        Logger.debug(f"  - 缓存命中: {cache_hits}")
        Logger.debug(f"  - 缓存未命中: {cache_misses}")
        Logger.debug(f"  - 缓存命中率: {cache_hit_rate:.2%}")
        Logger.debug(f"  - 缓存检查耗时: {cache_check_time:.3f}秒")
        
        # 如果有需要向量化的文本
        api_call_time = 0
        cache_store_time = 0
        
        if embedding_indices:
            # 提取需要向量化的文本
            texts_to_embed = [texts[i] for i in embedding_indices]
            
            Logger.debug(f"需要API向量化: {len(texts_to_embed)} 个文本")
            
            try:
                # 调用API进行向量化
                api_start_time = time.time()
                api_embeddings = await self._call_embedding_api(texts_to_embed)
                api_call_time = time.time() - api_start_time
                
                # 处理结果和缓存
                cache_start_time = time.time()
                for idx, embedding in zip(embedding_indices, api_embeddings):
                    embeddings[idx] = embedding
                    
                    # 缓存结果
                    text_hash = self._generate_hash(texts[idx])
                    cache_key = f"embedding:doc:{self.provider}:{self.model}:{text_hash}"
                    await redis_manager.set(
                        cache_key,
                        json.dumps(embedding),
                        expire=timedelta(days=7)
                    )
                cache_store_time = time.time() - cache_start_time
                
                Logger.debug(f"API向量化完成:")
                Logger.debug(f"  - API调用耗时: {api_call_time:.3f}秒")
                Logger.debug(f"  - 缓存存储耗时: {cache_store_time:.3f}秒")
                
            except Exception as e:
                Logger.error(f"向量化文档失败: {str(e)}")
                raise
        
        # 计算总处理时间
        total_time = time.time() - start_time
        
        # 过滤None值
        result_embeddings = [e for e in embeddings if e is not None]
        
        # 记录缓存向量化完成
        Logger.debug(f"缓存向量化完成:")
        Logger.debug(f"  - 输入文本数: {len(texts)}")
        Logger.debug(f"  - 输出向量数: {len(result_embeddings)}")
        Logger.debug(f"  - 缓存命中率: {cache_hit_rate:.2%}")
        Logger.debug(f"  - 总耗时: {total_time:.3f}秒")
        Logger.debug(f"  - 缓存节省时间: {api_call_time * cache_hit_rate:.3f}秒")
        
        # 记录性能指标
        Logger.rag_performance_metrics(
            operation="cached_embed_documents",
            duration=total_time,
            input_text_count=len(texts),
            output_vector_count=len(result_embeddings),
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            cache_hit_rate=cache_hit_rate,
            cache_check_time=cache_check_time,
            api_call_time=api_call_time,
            cache_store_time=cache_store_time,
            model=self.model,
            provider=self.provider
        )
                
        return result_embeddings
        
    async def embed_query(self, text: str) -> List[float]:
        """向量化查询
        
        Args:
            text: 查询文本
            
        Returns:
            List[float]: 查询向量
        """
        start_time = time.time()
        
        # 记录查询向量化开始
        query_preview = text[:50] + "..." if len(text) > 50 else text
        Logger.debug(f"开始缓存向量化查询: '{query_preview}'")
        
        # 生成缓存键
        text_hash = self._generate_hash(text)
        cache_key = f"embedding:query:{self.provider}:{self.model}:{text_hash}"
        
        # 尝试从缓存获取
        cache_check_start = time.time()
        cached = await redis_manager.get(cache_key)
        cache_check_time = time.time() - cache_check_start
        
        if cached:
            try:
                embedding = json.loads(cached)
                cache_parse_time = time.time() - cache_check_start - cache_check_time
                total_time = time.time() - start_time
                
                Logger.debug(f"查询向量缓存命中:")
                Logger.debug(f"  - 缓存检查耗时: {cache_check_time:.3f}秒")
                Logger.debug(f"  - 缓存解析耗时: {cache_parse_time:.3f}秒")
                Logger.debug(f"  - 总耗时: {total_time:.3f}秒")
                
                # 记录缓存命中的性能指标
                Logger.rag_performance_metrics(
                    operation="cached_embed_query_hit",
                    duration=total_time,
                    query_length=len(text),
                    cache_check_time=cache_check_time,
                    cache_parse_time=cache_parse_time,
                    model=self.model,
                    provider=self.provider
                )
                
                return embedding
            except Exception as e:
                Logger.warning(f"解析缓存查询向量失败: {str(e)}")
                # 如果解析失败，继续调用API
                
        # 缓存未命中，调用API
        Logger.debug(f"查询向量缓存未命中，调用API")
        
        try:
            # 调用API进行向量化
            api_start_time = time.time()
            embeddings = await self._call_embedding_api([text])
            embedding = embeddings[0]
            api_call_time = time.time() - api_start_time
            
            # 缓存结果
            cache_store_start = time.time()
            await redis_manager.set(
                cache_key,
                json.dumps(embedding),
                expire=timedelta(hours=24)  # 查询向量缓存时间较短
            )
            cache_store_time = time.time() - cache_store_start
            
            total_time = time.time() - start_time
            
            Logger.debug(f"查询向量API调用完成:")
            Logger.debug(f"  - API调用耗时: {api_call_time:.3f}秒")
            Logger.debug(f"  - 缓存存储耗时: {cache_store_time:.3f}秒")
            Logger.debug(f"  - 总耗时: {total_time:.3f}秒")
            
            # 记录API调用的性能指标
            Logger.rag_performance_metrics(
                operation="cached_embed_query_miss",
                duration=total_time,
                query_length=len(text),
                cache_check_time=cache_check_time,
                api_call_time=api_call_time,
                cache_store_time=cache_store_time,
                model=self.model,
                provider=self.provider
            )
            
            return embedding
        except Exception as e:
            total_time = time.time() - start_time
            Logger.error(f"向量化查询失败: {str(e)}")
            
            # 记录失败的性能指标
            Logger.rag_performance_metrics(
                operation="cached_embed_query_failed",
                duration=total_time,
                query_length=len(text),
                cache_check_time=cache_check_time,
                error=str(e),
                error_type=type(e).__name__,
                model=self.model,
                provider=self.provider
            )
            
            raise
            
    async def _call_embedding_api(self, texts: List[str]) -> List[List[float]]:
        """调用嵌入模型API
        
        Args:
            texts: 文本列表
            
        Returns:
            List[List[float]]: 向量列表
        """
        start_time = time.time()
        
        # 记录API调用开始
        total_text_length = sum(len(text) for text in texts)
        Logger.debug(f"开始调用嵌入模型API:")
        Logger.debug(f"  - 文本数量: {len(texts)}")
        Logger.debug(f"  - 总文本长度: {total_text_length}")
        Logger.debug(f"  - 模型: {self.model}")
        Logger.debug(f"  - 提供商: {self.provider}")
        Logger.debug(f"  - API基础URL: {self.api_base}")
        
        # 记录API调用配置
        Logger.rag_performance_metrics(
            operation="embedding_api_call_start",
            duration=0.0,
            text_count=len(texts),
            total_text_length=total_text_length,
            model=self.model,
            provider=self.provider,
            api_base=self.api_base
        )
        
        try:
            import httpx
            
            # 准备请求数据
            request_prep_start = time.time()
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            data = {
                "input": texts,
                "model": self.model
            }
            request_prep_time = time.time() - request_prep_start
            
            # 发送请求
            request_start = time.time()
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/embeddings",
                    headers=headers,
                    json=data,
                    timeout=60.0
                )
            request_time = time.time() - request_start
                
            # 检查响应
            if response.status_code != 200:
                error_msg = f"API请求失败: {response.status_code} {response.text}"
                Logger.error(error_msg)
                
                # 记录API错误
                Logger.rag_performance_metrics(
                    operation="embedding_api_call_error",
                    duration=time.time() - start_time,
                    text_count=len(texts),
                    status_code=response.status_code,
                    error=error_msg,
                    model=self.model,
                    provider=self.provider
                )
                
                raise Exception(error_msg)
                
            # 解析响应
            parse_start = time.time()
            result = response.json()
            
            # 提取向量
            embeddings = []
            vector_norms = []
            
            for item in result["data"]:
                # 归一化向量
                vector = np.array(item["embedding"])
                original_norm = np.linalg.norm(vector)
                normalized = (vector / original_norm).tolist()
                embeddings.append(normalized)
                vector_norms.append(original_norm)
            
            parse_time = time.time() - parse_start
            total_time = time.time() - start_time
            
            # 计算向量质量指标
            if vector_norms:
                avg_norm = sum(vector_norms) / len(vector_norms)
                min_norm = min(vector_norms)
                max_norm = max(vector_norms)
                vector_dim = len(embeddings[0]) if embeddings else 0
            else:
                avg_norm = min_norm = max_norm = vector_dim = 0
            
            # 记录API调用成功
            Logger.debug(f"嵌入模型API调用成功:")
            Logger.debug(f"  - 响应状态码: {response.status_code}")
            Logger.debug(f"  - 返回向量数: {len(embeddings)}")
            Logger.debug(f"  - 向量维度: {vector_dim}")
            Logger.debug(f"  - 平均向量范数: {avg_norm:.4f}")
            Logger.debug(f"  - 向量范数范围: [{min_norm:.4f}, {max_norm:.4f}]")
            Logger.debug(f"  - 请求准备耗时: {request_prep_time:.3f}秒")
            Logger.debug(f"  - 网络请求耗时: {request_time:.3f}秒")
            Logger.debug(f"  - 响应解析耗时: {parse_time:.3f}秒")
            Logger.debug(f"  - 总耗时: {total_time:.3f}秒")
            Logger.debug(f"  - 处理速度: {len(texts)/total_time:.1f} 文本/秒")
            
            # 记录API调用成功的性能指标
            Logger.rag_performance_metrics(
                operation="embedding_api_call_success",
                duration=total_time,
                text_count=len(texts),
                total_text_length=total_text_length,
                vector_count=len(embeddings),
                vector_dimension=vector_dim,
                avg_vector_norm=avg_norm,
                min_vector_norm=min_norm,
                max_vector_norm=max_norm,
                request_prep_time=request_prep_time,
                network_request_time=request_time,
                response_parse_time=parse_time,
                processing_speed=len(texts)/total_time if total_time > 0 else 0,
                status_code=response.status_code,
                model=self.model,
                provider=self.provider
            )
                
            return embeddings
            
        except Exception as e:
            total_time = time.time() - start_time
            
            import traceback
            error_info = traceback.format_exc()
            
            Logger.error(f"调用嵌入模型API失败:")
            Logger.error(f"  - 文本数量: {len(texts)}")
            Logger.error(f"  - 模型: {self.model}")
            Logger.error(f"  - 提供商: {self.provider}")
            Logger.error(f"  - 错误信息: {str(e)}")
            Logger.debug(f"堆栈跟踪:\n{error_info}")
            
            # 记录API调用失败的性能指标
            Logger.rag_performance_metrics(
                operation="embedding_api_call_failed",
                duration=total_time,
                text_count=len(texts),
                total_text_length=total_text_length,
                model=self.model,
                provider=self.provider,
                error=str(e),
                error_type=type(e).__name__
            )
            
            raise
            
    def _generate_hash(self, text: str) -> str:
        """生成文本哈希值
        
        Args:
            text: 文本
            
        Returns:
            str: 哈希值
        """
        return hashlib.md5(text.encode()).hexdigest()