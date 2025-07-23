"""检索引擎"""
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session

from app.core.logger import Logger
from app.schemas.llm import LLMConfig
from app.models.knowledge_base import KnowledgeBase
from app.rag.models.document import Document
from app.rag.retrieval.retrieval_methods import RetrievalMethod
from app.rag.embedding.embedding_engine import EmbeddingEngine
from app.rag.index_processor.index_processor_factory import IndexProcessorFactory

class RetrievalEngine:
    """检索引擎
    
    负责执行向量检索和关键词检索
    """
    
    def __init__(self, db: Session, llm_config: LLMConfig):
        """初始化检索引擎
        
        Args:
            db: 数据库会话
            llm_config: LLM配置
        """
        self.db = db
        self.llm_config = llm_config
        self.embedding_engine = EmbeddingEngine(llm_config)
        
    async def semantic_search(
        self,
        knowledge_base: KnowledgeBase,
        query: str,
        top_k: int = 5,
        **kwargs
    ) -> List[Document]:
        """语义搜索
        
        Args:
            knowledge_base: 知识库对象
            query: 查询文本
            top_k: 返回结果数量
            **kwargs: 其他参数
            
        Returns:
            List[Document]: 检索结果
        """
        try:
            # 创建索引处理器
            index_processor = IndexProcessorFactory.create_index_processor(knowledge_base)
            
            # 执行检索
            results = await index_processor.retrieve(
                knowledge_base=knowledge_base,
                query=query,
                top_k=top_k,
                llm_config=self.llm_config,
                db=self.db,
                **kwargs
            )
            
            return results
            
        except Exception as e:
            Logger.error(f"语义搜索失败: {str(e)}")
            return []
            
    async def keyword_search(
        self,
        knowledge_base: KnowledgeBase,
        query: str,
        top_k: int = 5,
        **kwargs
    ) -> List[Document]:
        """关键词搜索
        
        Args:
            knowledge_base: 知识库对象
            query: 查询文本
            top_k: 返回结果数量
            **kwargs: 其他参数
            
        Returns:
            List[Document]: 检索结果
        """
        try:
            # 强制使用关键词索引处理器
            from app.rag.index_processor.keyword_index_processor import KeywordIndexProcessor
            index_processor = KeywordIndexProcessor()
            
            # 执行检索
            results = await index_processor.retrieve(
                knowledge_base=knowledge_base,
                query=query,
                top_k=top_k,
                db=self.db,
                **kwargs
            )
            
            return results
            
        except Exception as e:
            Logger.error(f"关键词搜索失败: {str(e)}")
            return []
            
    async def hybrid_search(
        self,
        knowledge_base: KnowledgeBase,
        query: str,
        top_k: int = 5,
        **kwargs
    ) -> List[Document]:
        """混合搜索
        
        Args:
            knowledge_base: 知识库对象
            query: 查询文本
            top_k: 返回结果数量
            **kwargs: 其他参数
            
        Returns:
            List[Document]: 检索结果
        """
        try:
            # 执行语义搜索
            semantic_results = await self.semantic_search(
                knowledge_base=knowledge_base,
                query=query,
                top_k=top_k,
                **kwargs
            )
            
            # 执行关键词搜索
            keyword_results = await self.keyword_search(
                knowledge_base=knowledge_base,
                query=query,
                top_k=top_k,
                **kwargs
            )
            
            # 合并结果
            merged_results = self._merge_results(semantic_results, keyword_results, top_k)
            
            return merged_results
            
        except Exception as e:
            Logger.error(f"混合搜索失败: {str(e)}")
            return []
            
    def _merge_results(
        self,
        semantic_results: List[Document],
        keyword_results: List[Document],
        top_k: int
    ) -> List[Document]:
        """合并检索结果
        
        Args:
            semantic_results: 语义搜索结果
            keyword_results: 关键词搜索结果
            top_k: 返回结果数量
            
        Returns:
            List[Document]: 合并后的检索结果
        """
        try:
            # 创建结果字典，以文档ID为键
            result_dict = {}
            
            # 处理语义搜索结果
            for doc in semantic_results:
                doc_id = doc.metadata.get("doc_id")
                if doc_id:
                    result_dict[doc_id] = doc
                    # 设置语义搜索分数
                    doc.metadata["semantic_score"] = doc.metadata.get("score", 0.0)
                    
            # 处理关键词搜索结果
            for doc in keyword_results:
                doc_id = doc.metadata.get("doc_id")
                if doc_id:
                    if doc_id in result_dict:
                        # 如果文档已存在，更新关键词搜索分数
                        result_dict[doc_id].metadata["keyword_score"] = doc.metadata.get("score", 0.0)
                    else:
                        # 如果文档不存在，添加到结果字典
                        doc.metadata["keyword_score"] = doc.metadata.get("score", 0.0)
                        doc.metadata["semantic_score"] = 0.0
                        result_dict[doc_id] = doc
                        
            # 计算混合分数
            for doc_id, doc in result_dict.items():
                semantic_score = doc.metadata.get("semantic_score", 0.0)
                keyword_score = doc.metadata.get("keyword_score", 0.0)
                # 混合分数 = 0.7 * 语义分数 + 0.3 * 关键词分数
                hybrid_score = 0.7 * semantic_score + 0.3 * keyword_score
                doc.metadata["score"] = hybrid_score
                
            # 按混合分数排序
            results = list(result_dict.values())
            results.sort(key=lambda x: x.metadata.get("score", 0.0), reverse=True)
            
            # 返回前top_k个结果
            return results[:top_k]
            
        except Exception as e:
            Logger.error(f"合并检索结果失败: {str(e)}")
            return semantic_results[:top_k]  # 如果合并失败，返回语义搜索结果
            
    async def search(
        self,
        knowledge_base: KnowledgeBase,
        query: str,
        method: str = RetrievalMethod.SEMANTIC_SEARCH,
        top_k: int = 5,
        **kwargs
    ) -> List[Document]:
        """搜索
        
        Args:
            knowledge_base: 知识库对象
            query: 查询文本
            method: 检索方法
            top_k: 返回结果数量
            **kwargs: 其他参数
            
        Returns:
            List[Document]: 检索结果
        """
        try:
            # 根据检索方法选择检索函数
            if method == RetrievalMethod.SEMANTIC_SEARCH:
                return await self.semantic_search(knowledge_base, query, top_k, **kwargs)
            elif method == RetrievalMethod.KEYWORD_SEARCH:
                return await self.keyword_search(knowledge_base, query, top_k, **kwargs)
            elif method == RetrievalMethod.HYBRID_SEARCH:
                return await self.hybrid_search(knowledge_base, query, top_k, **kwargs)
            else:
                Logger.warning(f"未知的检索方法: {method}，使用语义搜索")
                return await self.semantic_search(knowledge_base, query, top_k, **kwargs)
                
        except Exception as e:
            Logger.error(f"搜索失败: {str(e)}")
            return []