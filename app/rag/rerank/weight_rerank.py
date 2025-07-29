"""加权重排序器"""
import math
from collections import Counter
from typing import Optional, List, Dict, Any

import numpy as np

from app.rag.models.document import Document
from app.rag.rerank.rerank_base import BaseRerankRunner
from app.rag.rerank.entity.weight import Weights, VectorSetting
try:
    from app.rag.keyword.jieba_keyword_handler import JiebaKeywordHandler
except ImportError:
    # 如果jieba不可用，使用简单的关键词提取器
    import re
    from typing import Set
    
    class JiebaKeywordHandler:
        def extract_keywords(self, text: str, stopwords: Optional[Set[str]] = None) -> List[str]:
            if not text:
                return []
            # 简单分词
            words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text)
            default_stopwords = {'的', '是', '在', '了', '和', '与', '或', '但', '而', '也', '都', '很', '更', '最'}
            if stopwords:
                default_stopwords.update(stopwords)
            keywords = []
            for word in words:
                if word not in default_stopwords and len(word) > 1:
                    keywords.append(word.lower())
            return keywords
from app.rag.embedding.cached_embedding import CacheEmbedding
from app.core.logger import Logger


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
    
    async def run(
        self,
        query: str,
        documents: List[Document],
        score_threshold: Optional[float] = None,
        top_n: Optional[int] = None,
        user_id: Optional[str] = None,
    ) -> List[Document]:
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
        import time
        start_time = time.time()
        
        Logger.info("开始加权重排序", extra={
            "user_id": self.user_id,
            "query_length": len(query),
            "document_count": len(documents),
            "score_threshold": score_threshold,
            "top_n": top_n,
            "vector_weight": self.weights.vector_setting.vector_weight,
            "keyword_weight": self.weights.keyword_setting.keyword_weight
        })
        
        # 去重文档
        unique_documents = []
        doc_ids = set()
        duplicate_count = 0
        
        for document in documents:
            doc_id = document.metadata.get("doc_id")
            if doc_id and doc_id not in doc_ids:
                doc_ids.add(doc_id)
                unique_documents.append(document)
            elif doc_id is None and document not in unique_documents:
                unique_documents.append(document)
            else:
                duplicate_count += 1
        
        documents = unique_documents
        
        Logger.info("文档去重完成", extra={
            "user_id": self.user_id,
            "original_count": len(documents) + duplicate_count,
            "unique_count": len(documents),
            "duplicate_count": duplicate_count
        })
        
        try:
            # 计算关键词分数
            keyword_start_time = time.time()
            keyword_scores = self._calculate_keyword_score(query, documents)
            keyword_duration = time.time() - keyword_start_time
            
            Logger.info("关键词分数计算完成", extra={
                "user_id": self.user_id,
                "duration": keyword_duration,
                "document_count": len(documents),
                "avg_keyword_score": sum(keyword_scores) / len(keyword_scores) if keyword_scores else 0,
                "max_keyword_score": max(keyword_scores) if keyword_scores else 0,
                "min_keyword_score": min(keyword_scores) if keyword_scores else 0
            })
            
            # 计算向量相似度分数
            vector_start_time = time.time()
            vector_scores = await self._calculate_vector_similarity(query, documents, self.weights.vector_setting)
            vector_duration = time.time() - vector_start_time
            
            Logger.info("向量相似度计算完成", extra={
                "user_id": self.user_id,
                "duration": vector_duration,
                "document_count": len(documents),
                "avg_vector_score": sum(vector_scores) / len(vector_scores) if vector_scores else 0,
                "max_vector_score": max(vector_scores) if vector_scores else 0,
                "min_vector_score": min(vector_scores) if vector_scores else 0
            })
            
        except Exception as e:
            Logger.error(f"计算重排序分数失败: {str(e)}", extra={
                "user_id": self.user_id,
                "query_length": len(query),
                "document_count": len(documents),
                "error_type": type(e).__name__
            })
            # 如果计算失败，返回原始文档
            return documents[:top_n] if top_n else documents
        
        # 组合分数
        rerank_documents = []
        filtered_count = 0
        
        for document, keyword_score, vector_score in zip(documents, keyword_scores, vector_scores):
            # 计算加权分数
            score = (
                self.weights.vector_setting.vector_weight * vector_score
                + self.weights.keyword_setting.keyword_weight * keyword_score
            )
            
            # 过滤低分文档
            if score_threshold and score < score_threshold:
                filtered_count += 1
                continue
                
            # 更新文档分数
            document.metadata["score"] = score
            document.metadata["keyword_score"] = keyword_score
            document.metadata["vector_score"] = vector_score
            rerank_documents.append(document)
        
        # 按分数排序
        rerank_documents.sort(key=lambda x: x.metadata.get("score", 0.0), reverse=True)
        
        # 应用top_n限制
        final_documents = rerank_documents[:top_n] if top_n else rerank_documents
        
        total_duration = time.time() - start_time
        
        Logger.info("加权重排序完成", extra={
            "user_id": self.user_id,
            "total_duration": total_duration,
            "keyword_duration": keyword_duration,
            "vector_duration": vector_duration,
            "original_count": len(documents),
            "filtered_count": filtered_count,
            "reranked_count": len(rerank_documents),
            "final_count": len(final_documents),
            "avg_final_score": sum(doc.metadata.get("score", 0) for doc in final_documents) / len(final_documents) if final_documents else 0,
            "top_score": final_documents[0].metadata.get("score", 0) if final_documents else 0
        })
        
        # 记录性能指标
        Logger.rag_performance_metrics(
            operation="weight_rerank",
            duration=total_duration,
            user_id=self.user_id,
            keyword_calculation_duration=keyword_duration,
            vector_calculation_duration=vector_duration,
            documents_processed=len(documents),
            documents_filtered=filtered_count,
            documents_returned=len(final_documents),
            avg_score=sum(doc.metadata.get("score", 0) for doc in final_documents) / len(final_documents) if final_documents else 0
        )
        
        # 返回结果
        return final_documents
    
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
        
        Logger.debug("提取查询关键词", extra={
            "user_id": self.user_id,
            "query": query,
            "query_keywords": query_keywords,
            "keyword_count": len(query_keywords)
        })
        
        # 提取文档关键词
        documents_keywords = []
        total_doc_keywords = 0
        
        for document in documents:
            document_keywords = self.keyword_handler.extract_keywords(document.page_content, None)
            document.metadata["keywords"] = document_keywords
            documents_keywords.append(document_keywords)
            total_doc_keywords += len(document_keywords)
        
        Logger.debug("提取文档关键词完成", extra={
            "user_id": self.user_id,
            "document_count": len(documents),
            "total_keywords": total_doc_keywords,
            "avg_keywords_per_doc": total_doc_keywords / len(documents) if documents else 0
        })
        
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
        
        Logger.debug("IDF计算完成", extra={
            "user_id": self.user_id,
            "unique_keywords": len(all_keywords),
            "avg_idf": sum(keyword_idf.values()) / len(keyword_idf) if keyword_idf else 0,
            "max_idf": max(keyword_idf.values()) if keyword_idf else 0,
            "min_idf": min(keyword_idf.values()) if keyword_idf else 0
        })
        
        # 计算BM25分数
        k1 = self.weights.keyword_setting.k1
        b = self.weights.keyword_setting.b
        
        # 计算平均文档长度
        avg_doc_length = sum(len(doc_keywords) for doc_keywords in documents_keywords) / total_documents if total_documents > 0 else 0
        
        Logger.debug("BM25参数", extra={
            "user_id": self.user_id,
            "k1": k1,
            "b": b,
            "avg_doc_length": avg_doc_length,
            "total_documents": total_documents
        })
        
        # 计算每个文档的分数
        scores = []
        matched_keywords_stats = []
        
        for doc_idx, doc_keywords in enumerate(documents_keywords):
            score = 0.0
            doc_length = len(doc_keywords)
            matched_keywords = 0
            
            # 统计文档关键词频率
            doc_keyword_counts = Counter(doc_keywords)
            
            # 计算每个查询关键词的分数
            for query_keyword, query_count in query_keyword_counts.items():
                if query_keyword in doc_keyword_counts:
                    matched_keywords += 1
                    # 文档中关键词出现次数
                    doc_count = doc_keyword_counts[query_keyword]
                    
                    # 获取IDF
                    idf = keyword_idf.get(query_keyword, 0.0)
                    
                    # BM25公式
                    numerator = doc_count * (k1 + 1)
                    denominator = doc_count + k1 * (1 - b + b * doc_length / avg_doc_length if avg_doc_length > 0 else 1)
                    keyword_score = idf * numerator / denominator
                    score += keyword_score
            
            scores.append(score)
            matched_keywords_stats.append(matched_keywords)
        
        Logger.debug("BM25分数计算完成", extra={
            "user_id": self.user_id,
            "avg_score": sum(scores) / len(scores) if scores else 0,
            "max_score": max(scores) if scores else 0,
            "min_score": min(scores) if scores else 0,
            "avg_matched_keywords": sum(matched_keywords_stats) / len(matched_keywords_stats) if matched_keywords_stats else 0,
            "total_query_keywords": len(query_keywords)
        })
        
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
        Logger.debug("开始计算查询向量", extra={
            "user_id": self.user_id,
            "query_length": len(query)
        })
        
        query_vector = await self.embedding_engine.embed_query(query)
        
        Logger.debug("查询向量计算完成", extra={
            "user_id": self.user_id,
            "vector_dimension": len(query_vector) if query_vector else 0,
            "vector_norm": np.linalg.norm(query_vector) if query_vector else 0
        })
        
        # 计算每个文档的相似度
        scores = []
        documents_with_vectors = 0
        documents_need_embedding = 0
        
        for doc_idx, document in enumerate(documents):
            # 如果文档已有向量，直接使用
            if document.vector:
                document_vector = document.vector
                documents_with_vectors += 1
            else:
                # 否则，计算文档向量
                documents_need_embedding += 1
                document_vectors = await self.embedding_engine.embed_documents([document.page_content])
                document_vector = document_vectors[0] if document_vectors else None
                document.vector = document_vector
            
            # 计算相似度
            similarity = cosine_similarity(query_vector, document_vector)
            scores.append(similarity)
        
        Logger.debug("向量相似度计算完成", extra={
            "user_id": self.user_id,
            "total_documents": len(documents),
            "documents_with_vectors": documents_with_vectors,
            "documents_need_embedding": documents_need_embedding,
            "avg_similarity": sum(scores) / len(scores) if scores else 0,
            "max_similarity": max(scores) if scores else 0,
            "min_similarity": min(scores) if scores else 0
        })
        
        return scores 