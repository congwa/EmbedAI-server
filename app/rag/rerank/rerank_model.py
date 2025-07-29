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
        import time
        start_time = time.time()
        
        Logger.info("开始模型重排序", extra={
            "user_id": user_id,
            "query_length": len(query),
            "document_count": len(documents),
            "score_threshold": score_threshold,
            "top_n": top_n,
            "model_type": type(self.model_instance).__name__
        })
        
        # 去重文档
        docs = []
        doc_ids = set()
        unique_documents = []
        duplicate_count = 0
        
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
                else:
                    duplicate_count += 1
            else:
                duplicate_count += 1
        
        documents = unique_documents
        
        Logger.info("文档去重完成", extra={
            "user_id": user_id,
            "original_count": len(documents) + duplicate_count,
            "unique_count": len(documents),
            "duplicate_count": duplicate_count
        })
        
        try:
            # 调用重排序模型
            model_start_time = time.time()
            
            Logger.debug("调用重排序模型", extra={
                "user_id": user_id,
                "model_type": type(self.model_instance).__name__,
                "query": query,
                "document_count": len(docs)
            })
            
            rerank_result = await self.model_instance.invoke_rerank(
                query=query, 
                docs=docs, 
                score_threshold=score_threshold, 
                top_n=top_n, 
                user=user_id
            )
            
            model_duration = time.time() - model_start_time
            
            Logger.info("重排序模型调用完成", extra={
                "user_id": user_id,
                "model_duration": model_duration,
                "result_count": len(rerank_result.docs) if hasattr(rerank_result, 'docs') else 0
            })
            
        except Exception as e:
            Logger.error(f"调用重排序模型失败: {str(e)}", extra={
                "user_id": user_id,
                "model_type": type(self.model_instance).__name__,
                "query_length": len(query),
                "document_count": len(documents),
                "error_type": type(e).__name__
            })
            # 如果调用失败，返回原始文档
            return documents[:top_n] if top_n else documents
        
        # 处理重排序结果
        rerank_documents = []
        filtered_count = 0
        
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
            else:
                filtered_count += 1
        
        # 按分数排序
        rerank_documents.sort(key=lambda x: x.metadata.get("score", 0.0), reverse=True)
        
        # 应用top_n限制
        final_documents = rerank_documents[:top_n] if top_n else rerank_documents
        
        total_duration = time.time() - start_time
        
        Logger.info("模型重排序完成", extra={
            "user_id": user_id,
            "total_duration": total_duration,
            "model_duration": model_duration,
            "original_count": len(documents),
            "reranked_count": len(rerank_documents),
            "filtered_count": filtered_count,
            "final_count": len(final_documents),
            "avg_score": sum(doc.metadata.get("score", 0) for doc in final_documents) / len(final_documents) if final_documents else 0,
            "top_score": final_documents[0].metadata.get("score", 0) if final_documents else 0
        })
        
        # 记录性能指标
        Logger.rag_performance_metrics(
            operation="model_rerank",
            duration=total_duration,
            user_id=user_id,
            model_duration=model_duration,
            documents_processed=len(documents),
            documents_filtered=filtered_count,
            documents_returned=len(final_documents),
            avg_score=sum(doc.metadata.get("score", 0) for doc in final_documents) / len(final_documents) if final_documents else 0,
            model_type=type(self.model_instance).__name__
        )
        
        # 返回结果
        return final_documents 