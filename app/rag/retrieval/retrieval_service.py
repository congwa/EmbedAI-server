"""检索服务"""
from typing import List, Dict, Any, Optional, Tuple

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
            **kwargs: 其他参数
            
        Returns:
            List[Dict[str, Any]]: 检索结果
        """
        try:
            # 创建检索引擎
            retrieval_engine = RetrievalEngine(self.db, llm_config)
            
            # 执行检索
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
            
            # 格式化结果
            formatted_results = await self._format_results(results)
            
            return formatted_results
            
        except Exception as e:
            Logger.error(f"查询知识库失败: {str(e)}")
            return []
            
    async def _format_results(self, results: List[Document]) -> List[Dict[str, Any]]:
        """格式化检索结果
        
        Args:
            results: 检索结果
            
        Returns:
            List[Dict[str, Any]]: 格式化后的检索结果
        """
        try:
            formatted_results = []
            
            for doc in results:
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
                
            return formatted_results
            
        except Exception as e:
            Logger.error(f"格式化检索结果失败: {str(e)}")
            return [{"content": doc.page_content, "score": doc.metadata.get("score", 0.0)} for doc in results]