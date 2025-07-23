"""加权重排序器"""
import math
from collections import Counter
from typing import Optional, List, Dict, Any

import numpy as np

from app.rag.models.document import Document
from app.rag.rerank.rerank_base import BaseRerankRunner
from app.rag.rerank.entity.weight import Weights, VectorSetting
from app.rag.keyword.jieba_keyword_handler import JiebaKeywordHandler
from app.rag.embedding.cached_embedding import CacheEmbedding


class WeightRerankRunner(BaseRerankRunner):
    """加权重排序器"""
    
    def __init__(self, user_id: str, weights: Weights, embedding_engine: CacheEmbedding) -> None:
        """
        初始化
        
        Args:
            user_id: 用户ID
            weights: 重排序权重
            embedding_engine: 向量引擎
        """
        self.user_id = user_id
        self.weights = weights
        self.embedding_engine = embedding_engine
        self.keyword_handler = JiebaKeywordHandler()
    
    def run(
        self,
        query: str,
        documents: list[Document],
        score_threshold: Optional[float] = None,
        top_n: Optional[int] = None,
        user_id: Optional[str] = None,
    ) -> list[Document]:
        """
        运行重排序
        
        Args:
            query: 查询文本
            documents: 待重排序的文档列表
            score_threshold: 分数阈值，低于此分数的文档将被过滤
            top_n: 返回的最大文档数量
            user_id: 用户ID（如果需要）
            
        Returns:
            重排序后的文档列表
        """
        # 去重文档
        unique_documents = []
        doc_ids = set()
        for document in documents:
            doc_id = document.metadata.get("doc_id")
            if doc_id and doc_id not in doc_ids:
                doc_ids.add(doc_id)
                unique_documents.append(document)
            elif doc_id is None and document not in unique_documents:
                unique_documents.append(document)
        
        documents = unique_documents
        
        # 计算关键词分数
        keyword_scores = self._calculate_keyword_score(query, documents)
        
        # 计算向量相似度分数
        vector_scores = self._calculate_vector_similarity(query, documents, self.weights.vector_setting)
        
        # 组合分数
        rerank_documents = []
        for document, keyword_score, vector_score in zip(documents, keyword_scores, vector_scores):
            # 计算加权分数
            score = (
                self.weights.vector_setting.vector_weight * vector_score
                + self.weights.keyword_setting.keyword_weight * keyword_score
            )
            
            # 过滤低分文档
            if score_threshold and score < score_threshold:
                continue
                
            # 更新文档分数
            document.metadata["score"] = score
            document.metadata["keyword_score"] = keyword_score
            document.metadata["vector_score"] = vector_score
            rerank_documents.append(document)
        
        # 按分数排序
        rerank_documents.sort(key=lambda x: x.metadata.get("score", 0.0), reverse=True)
        
        # 返回结果
        return rerank_documents[:top_n] if top_n else rerank_documents
    
    def _calculate_keyword_score(self, query: str, documents: List[Document]) -> List[float]:
        """
        计算关键词分数（BM25算法）
        
        Args:
            query: 查询文本
            documents: 文档列表
            
        Returns:
            关键词分数列表
        """
        # 提取查询关键词
        query_keywords = self.keyword_handler.extract_keywords(query, None)
        
        # 提取文档关键词
        documents_keywords = []
        for document in documents:
            document_keywords = self.keyword_handler.extract_keywords(document.page_content, None)
            document.metadata["keywords"] = document_keywords
            documents_keywords.append(document_keywords)
        
        # 统计查询关键词频率(TF)
        query_keyword_counts = Counter(query_keywords)
        
        # 文档总数
        total_documents = len(documents)
        
        # 计算所有文档关键词的IDF
        all_keywords = set()
        for document_keywords in documents_keywords:
            all_keywords.update(document_keywords)
        
        # 计算关键词IDF
        keyword_idf = {}
        for keyword in all_keywords:
            # 计算包含该关键词的文档数
            doc_count_containing_keyword = sum(1 for doc_keywords in documents_keywords if keyword in doc_keywords)
            # IDF公式
            keyword_idf[keyword] = math.log((1 + total_documents) / (1 + doc_count_containing_keyword)) + 1
        
        # 计算BM25分数
        k1 = self.weights.keyword_setting.k1
        b = self.weights.keyword_setting.b
        
        # 计算平均文档长度
        avg_doc_length = sum(len(doc_keywords) for doc_keywords in documents_keywords) / total_documents if total_documents > 0 else 0
        
        # 计算每个文档的分数
        scores = []
        for doc_idx, doc_keywords in enumerate(documents_keywords):
            score = 0.0
            doc_length = len(doc_keywords)
            
            # 统计文档关键词频率
            doc_keyword_counts = Counter(doc_keywords)
            
            # 计算每个查询关键词的分数
            for query_keyword, query_count in query_keyword_counts.items():
                if query_keyword in doc_keyword_counts:
                    # 文档中关键词出现次数
                    doc_count = doc_keyword_counts[query_keyword]
                    
                    # 获取IDF
                    idf = keyword_idf.get(query_keyword, 0.0)
                    
                    # BM25公式
                    numerator = doc_count * (k1 + 1)
                    denominator = doc_count + k1 * (1 - b + b * doc_length / avg_doc_length if avg_doc_length > 0 else 1)
                    score += idf * numerator / denominator
            
            scores.append(score)
        
        return scores
    
    async def _calculate_vector_similarity(self, query: str, documents: List[Document], vector_setting: VectorSetting) -> List[float]:
        """
        计算向量相似度
        
        Args:
            query: 查询文本
            documents: 文档列表
            vector_setting: 向量设置
            
        Returns:
            向量相似度列表
        """
        # 计算余弦相似度
        def cosine_similarity(vec1, vec2):
            # 确保向量不为空
            if not vec1 or not vec2:
                return 0.0
                
            # 转换为numpy数组
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            # 计算余弦相似度
            dot_product = np.dot(vec1, vec2)
            norm_vec1 = np.linalg.norm(vec1)
            norm_vec2 = np.linalg.norm(vec2)
            
            # 避免除零错误
            if norm_vec1 == 0 or norm_vec2 == 0:
                return 0.0
                
            return dot_product / (norm_vec1 * norm_vec2)
        
        # 获取查询向量
        query_vector = await self.embedding_engine.embed_query(query)
        
        # 计算每个文档的相似度
        scores = []
        for document in documents:
            # 如果文档已有向量，直接使用
            if document.vector:
                document_vector = document.vector
            else:
                # 否则，计算文档向量
                document_vectors = await self.embedding_engine.embed_documents([document.page_content])
                document_vector = document_vectors[0] if document_vectors else None
                document.vector = document_vector
            
            # 计算相似度
            similarity = cosine_similarity(query_vector, document_vector)
            scores.append(similarity)
        
        return scores 