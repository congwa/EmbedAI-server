"""模型重排序器"""
from typing import Optional, Dict, Any, List

from app.rag.models.document import Document
from app.rag.rerank.rerank_base import BaseRerankRunner
from app.core.logger import Logger


class RerankModelRunner(BaseRerankRunner):
    """模型重排序器"""
    
    def __init__(self, model_instance: Any) -> None:
        """
        初始化
        
        Args:
            model_instance: 重排序模型实例
        """
        self.model_instance = model_instance
    
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
        # 去重文档
        docs = []
        doc_ids = set()
        unique_documents = []
        
        for document in documents:
            doc_id = document.metadata.get("doc_id")
            if doc_id and doc_id not in doc_ids:
                doc_ids.add(doc_id)
                docs.append(document.page_content)
                unique_documents.append(document)
            elif doc_id is None:
                # 处理没有doc_id的文档
                if document not in unique_documents:
                    docs.append(document.page_content)
                    unique_documents.append(document)
        
        documents = unique_documents
        
        try:
            # 调用重排序模型
            rerank_result = await self.model_instance.invoke_rerank(
                query=query, 
                docs=docs, 
                score_threshold=score_threshold, 
                top_n=top_n, 
                user=user_id
            )
        except Exception as e:
            Logger.error(f"调用重排序模型失败: {str(e)}")
            # 如果调用失败，返回原始文档
            return documents[:top_n] if top_n else documents
        
        # 处理重排序结果
        rerank_documents = []
        
        for result in rerank_result.docs:
            if score_threshold is None or result.score >= score_threshold:
                # 格式化文档
                rerank_document = Document(
                    page_content=result.text,
                    metadata=documents[result.index].metadata,
                    vector=documents[result.index].vector
                )
                
                rerank_document.metadata["score"] = result.score
                rerank_documents.append(rerank_document)
        
        # 按分数排序
        rerank_documents.sort(key=lambda x: x.metadata.get("score", 0.0), reverse=True)
        
        # 返回结果
        return rerank_documents[:top_n] if top_n else rerank_documents 