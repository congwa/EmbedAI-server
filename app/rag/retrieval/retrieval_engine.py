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
from app.rag.rerank.rerank_factory import RerankRunnerFactory
from app.rag.rerank.rerank_type import RerankMode
from app.rag.rerank.entity.weight import Weights, VectorSetting, KeywordSetting
from app.rag.exceptions import RetrievalException, RerankException, EmbeddingException

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
        # 默认不使用重排序
        self.use_rerank = False
        self.rerank_mode = None
        self.rerank_model_instance = None
        
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
            
        except EmbeddingException as e:
            Logger.error(f"语义搜索向量化失败: {e.message}")
            raise RetrievalException(
                message=f"语义搜索向量化失败: {e.message}",
                knowledge_base_id=knowledge_base.id,
                method=RetrievalMethod.SEMANTIC_SEARCH,
                query=query,
                details=e.details
            )
        except Exception as e:
            Logger.error(f"语义搜索失败: {str(e)}")
            raise RetrievalException(
                message=f"语义搜索失败: {str(e)}",
                knowledge_base_id=knowledge_base.id,
                method=RetrievalMethod.SEMANTIC_SEARCH,
                query=query
            )
            
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
            raise RetrievalException(
                message=f"关键词搜索失败: {str(e)}",
                knowledge_base_id=knowledge_base.id,
                method=RetrievalMethod.KEYWORD_SEARCH,
                query=query
            )
            
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
            semantic_results = []
            keyword_results = []
            semantic_error = None
            keyword_error = None
            
            # 执行语义搜索
            try:
                semantic_results = await self.semantic_search(
                    knowledge_base=knowledge_base,
                    query=query,
                    top_k=top_k,
                    **kwargs
                )
            except RetrievalException as e:
                Logger.warning(f"混合搜索中的语义搜索失败: {e.message}")
                semantic_error = e
            
            # 执行关键词搜索
            try:
                keyword_results = await self.keyword_search(
                    knowledge_base=knowledge_base,
                    query=query,
                    top_k=top_k,
                    **kwargs
                )
            except RetrievalException as e:
                Logger.warning(f"混合搜索中的关键词搜索失败: {e.message}")
                keyword_error = e
            
            # 如果两种搜索都失败，抛出异常
            if not semantic_results and not keyword_results:
                error_message = "混合搜索失败: "
                if semantic_error:
                    error_message += f"语义搜索: {semantic_error.message}; "
                if keyword_error:
                    error_message += f"关键词搜索: {keyword_error.message}"
                    
                raise RetrievalException(
                    message=error_message,
                    knowledge_base_id=knowledge_base.id,
                    method=RetrievalMethod.HYBRID_SEARCH,
                    query=query
                )
            
            # 合并结果
            merged_results = self._merge_results(semantic_results, keyword_results, top_k)
            
            return merged_results
            
        except RetrievalException:
            # 重新抛出已经处理过的检索异常
            raise
        except Exception as e:
            Logger.error(f"混合搜索失败: {str(e)}")
            raise RetrievalException(
                message=f"混合搜索失败: {str(e)}",
                knowledge_base_id=knowledge_base.id,
                method=RetrievalMethod.HYBRID_SEARCH,
                query=query
            )
            
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
            
    def configure_rerank(
        self, 
        use_rerank: bool = False, 
        rerank_mode: str = RerankMode.WEIGHTED_SCORE,
        rerank_model_instance: Optional[Any] = None,
        user_id: Optional[str] = None
    ):
        """配置重排序
        
        Args:
            use_rerank: 是否使用重排序
            rerank_mode: 重排序模式
            rerank_model_instance: 重排序模型实例（用于模型重排序）
            user_id: 用户ID（用于加权重排序）
        """
        self.use_rerank = use_rerank
        self.rerank_mode = rerank_mode
        self.rerank_model_instance = rerank_model_instance
        self.user_id = user_id
        
    async def rerank_results(
        self,
        query: str,
        documents: List[Document],
        top_k: int = 5,
        score_threshold: Optional[float] = None
    ) -> List[Document]:
        """重排序结果
        
        Args:
            query: 查询文本
            documents: 检索结果
            top_k: 返回结果数量
            score_threshold: 分数阈值
            
        Returns:
            List[Document]: 重排序后的结果
        """
        try:
            if not self.use_rerank or not documents:
                return documents[:top_k]
                
            # 创建权重配置
            weights = RerankRunnerFactory.get_default_weights(
                model_name=self.llm_config.embeddings.model_name,
                model_provider=self.llm_config.embeddings.model_provider
            )
            
            # 创建重排序运行器
            try:
                rerank_runner = RerankRunnerFactory.create_rerank_runner(
                    rerank_mode=self.rerank_mode,
                    user_id=self.user_id,
                    model_instance=self.rerank_model_instance,
                    weights=weights,
                    embedding_engine=self.embedding_engine
                )
            except Exception as e:
                Logger.error(f"创建重排序运行器失败: {str(e)}")
                raise RerankException(
                    message=f"创建重排序运行器失败: {str(e)}",
                    rerank_mode=self.rerank_mode
                )
            
            # 执行重排序
            try:
                reranked_documents = await rerank_runner.run(
                    query=query,
                    documents=documents,
                    score_threshold=score_threshold,
                    top_n=top_k,
                    user_id=self.user_id
                )
                
                return reranked_documents
            except Exception as e:
                Logger.error(f"执行重排序失败: {str(e)}")
                raise RerankException(
                    message=f"执行重排序失败: {str(e)}",
                    rerank_mode=self.rerank_mode
                )
            
        except RerankException:
            # 重新抛出已经处理过的重排序异常
            Logger.warning(f"重排序失败，使用原始结果")
            return documents[:top_k]
        except Exception as e:
            Logger.error(f"重排序失败: {str(e)}")
            return documents[:top_k]
    
    async def search(
        self,
        knowledge_base: KnowledgeBase,
        query: str,
        method: str = RetrievalMethod.SEMANTIC_SEARCH,
        top_k: int = 5,
        use_rerank: bool = False,
        rerank_mode: str = RerankMode.WEIGHTED_SCORE,
        rerank_model_instance: Optional[Any] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> List[Document]:
        """搜索
        
        Args:
            knowledge_base: 知识库对象
            query: 查询文本
            method: 检索方法
            top_k: 返回结果数量
            use_rerank: 是否使用重排序
            rerank_mode: 重排序模式
            rerank_model_instance: 重排序模型实例
            user_id: 用户ID
            **kwargs: 其他参数
            
        Returns:
            List[Document]: 检索结果
        """
        try:
            # 配置重排序
            self.configure_rerank(use_rerank, rerank_mode, rerank_model_instance, user_id)
            
            # 根据检索方法选择检索函数
            try:
                if method == RetrievalMethod.SEMANTIC_SEARCH:
                    results = await self.semantic_search(knowledge_base, query, top_k, **kwargs)
                elif method == RetrievalMethod.KEYWORD_SEARCH:
                    results = await self.keyword_search(knowledge_base, query, top_k, **kwargs)
                elif method == RetrievalMethod.HYBRID_SEARCH:
                    results = await self.hybrid_search(knowledge_base, query, top_k, **kwargs)
                else:
                    Logger.warning(f"未知的检索方法: {method}，使用语义搜索")
                    results = await self.semantic_search(knowledge_base, query, top_k, **kwargs)
            except RetrievalException as e:
                Logger.error(f"检索失败: {e.message}")
                # 如果检索失败，返回空结果
                return []
            
            # 如果启用重排序，执行重排序
            if self.use_rerank and results:
                try:
                    results = await self.rerank_results(query, results, top_k, kwargs.get("score_threshold"))
                except RerankException as e:
                    Logger.warning(f"重排序失败: {e.message}，使用原始结果")
                    # 如果重排序失败，使用原始结果
                    results = results[:top_k]
                
            return results
                
        except Exception as e:
            Logger.error(f"搜索失败: {str(e)}")
            # 记录详细错误信息
            import traceback
            Logger.debug(f"搜索失败详细信息: {traceback.format_exc()}")
            return []