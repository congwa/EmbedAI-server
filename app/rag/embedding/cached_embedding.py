"""缓存向量化实现"""
import hashlib
import json
from typing import List, Optional, Dict, Any
import numpy as np
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
        self.provider = llm_config.embeddings.provider
        self.api_base = llm_config.embeddings.base_url
        self.api_key = llm_config.embeddings.api_key
        
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """向量化文档
        
        Args:
            texts: 文本列表
            
        Returns:
            List[List[float]]: 向量列表
        """
        # 初始化结果列表
        embeddings: List[Optional[List[float]]] = [None] * len(texts)
        
        # 需要向量化的文本索引
        embedding_indices = []
        
        # 检查缓存
        for i, text in enumerate(texts):
            text_hash = self._generate_hash(text)
            cache_key = f"embedding:doc:{self.provider}:{self.model}:{text_hash}"
            
            # 尝试从缓存获取
            cached = await redis_manager.get(cache_key)
            if cached:
                try:
                    embeddings[i] = json.loads(cached)
                except Exception as e:
                    Logger.error(f"解析缓存向量失败: {str(e)}")
                    embedding_indices.append(i)
            else:
                embedding_indices.append(i)
                
        # 如果有需要向量化的文本
        if embedding_indices:
            # 提取需要向量化的文本
            texts_to_embed = [texts[i] for i in embedding_indices]
            
            try:
                # 调用API进行向量化
                api_embeddings = await self._call_embedding_api(texts_to_embed)
                
                # 处理结果
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
            except Exception as e:
                Logger.error(f"向量化文档失败: {str(e)}")
                raise
                
        # 返回结果
        return [e for e in embeddings if e is not None]
        
    async def embed_query(self, text: str) -> List[float]:
        """向量化查询
        
        Args:
            text: 查询文本
            
        Returns:
            List[float]: 查询向量
        """
        # 生成缓存键
        text_hash = self._generate_hash(text)
        cache_key = f"embedding:query:{self.provider}:{self.model}:{text_hash}"
        
        # 尝试从缓存获取
        cached = await redis_manager.get(cache_key)
        if cached:
            try:
                return json.loads(cached)
            except Exception as e:
                Logger.error(f"解析缓存查询向量失败: {str(e)}")
                # 如果解析失败，继续调用API
                
        try:
            # 调用API进行向量化
            embeddings = await self._call_embedding_api([text])
            embedding = embeddings[0]
            
            # 缓存结果
            await redis_manager.set(
                cache_key,
                json.dumps(embedding),
                expire=timedelta(hours=24)  # 查询向量缓存时间较短
            )
            
            return embedding
        except Exception as e:
            Logger.error(f"向量化查询失败: {str(e)}")
            raise
            
    async def _call_embedding_api(self, texts: List[str]) -> List[List[float]]:
        """调用嵌入模型API
        
        Args:
            texts: 文本列表
            
        Returns:
            List[List[float]]: 向量列表
        """
        try:
            import httpx
            
            # 准备请求数据
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            data = {
                "input": texts,
                "model": self.model
            }
            
            # 发送请求
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/embeddings",
                    headers=headers,
                    json=data,
                    timeout=60.0
                )
                
            # 检查响应
            if response.status_code != 200:
                raise Exception(f"API请求失败: {response.status_code} {response.text}")
                
            # 解析响应
            result = response.json()
            
            # 提取向量
            embeddings = []
            for item in result["data"]:
                # 归一化向量
                vector = np.array(item["embedding"])
                normalized = (vector / np.linalg.norm(vector)).tolist()
                embeddings.append(normalized)
                
            return embeddings
            
        except Exception as e:
            Logger.error(f"调用嵌入模型API失败: {str(e)}")
            raise
            
    def _generate_hash(self, text: str) -> str:
        """生成文本哈希值
        
        Args:
            text: 文本
            
        Returns:
            str: 哈希值
        """
        return hashlib.md5(text.encode()).hexdigest()