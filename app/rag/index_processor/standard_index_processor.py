"""标准索引处理器"""

from typing import List, Dict, Any, Optional
import uuid
import json
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logger import Logger
from app.core.config import settings
from app.schemas.llm import LLMConfig
from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document as DBDocument
from app.models.document_chunk import DocumentChunk
from app.models.document_embedding import DocumentEmbedding
from app.rag.models.document import Document
from app.rag.index_processor.index_processor_base import BaseIndexProcessor
from app.rag.index_processor.index_cache import IndexCache
from app.rag.extractor.extract_processor import ExtractProcessor
from app.rag.cleaner.clean_processor import TextCleaner
from app.rag.splitter.recursive_character_text_splitter import (
    RecursiveCharacterTextSplitter,
)
from app.rag.embedding.embedding_engine import EmbeddingEngine
from app.rag.datasource.vdb.vector_factory import VectorFactory


class StandardIndexProcessor(BaseIndexProcessor):
    """标准索引处理器

    使用高质量的向量索引实现
    """

    def __init__(self):
        """初始化标准索引处理器"""
        self.extractor = ExtractProcessor()
        self.cleaner = TextCleaner()
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.RAG_CHUNK_SIZE, chunk_overlap=settings.RAG_CHUNK_OVERLAP
        )

        # 记录索引处理器初始化
        Logger.debug(f"初始化标准索引处理器:")
        Logger.debug(f"  - 分块大小: {settings.RAG_CHUNK_SIZE}")
        Logger.debug(f"  - 分块重叠: {settings.RAG_CHUNK_OVERLAP}")
        Logger.debug(f"  - 向量存储类型: {settings.RAG_VECTOR_STORE_TYPE}")

        # 记录初始化性能指标
        Logger.rag_performance_metrics(
            operation="standard_index_processor_init",
            duration=0.0,
            chunk_size=settings.RAG_CHUNK_SIZE,
            chunk_overlap=settings.RAG_CHUNK_OVERLAP,
            vector_store_type=settings.RAG_VECTOR_STORE_TYPE,
        )

    async def extract(self, document: DBDocument) -> List[Document]:
        """从文档中提取内容

        Args:
            document: 数据库文档对象

        Returns:
            List[Document]: 提取的文档对象列表
        """
        start_time = time.time()

        # 记录文档提取开始
        Logger.debug(f"开始提取文档内容:")
        Logger.debug(f"  - 文档ID: {document.id}")
        Logger.debug(f"  - 文档标题: {document.title}")
        Logger.debug(f"  - 文档类型: {document.file_type}")
        Logger.debug(f"  - 知识库ID: {document.knowledge_base_id}")

        try:
            # 提取文档内容
            extracted_documents = await self.extractor.process_document(document)

            # 计算处理时间
            process_time = time.time() - start_time

            # 如果没有提取到内容，返回空列表
            if not extracted_documents:
                Logger.warning(f"文档提取未产生内容:")
                Logger.warning(f"  - 文档ID: {document.id}")
                Logger.warning(f"  - 文档标题: {document.title}")
                Logger.warning(f"  - 处理耗时: {process_time:.3f}秒")

                # 记录空结果的性能指标
                Logger.rag_performance_metrics(
                    operation="document_extract_empty",
                    duration=process_time,
                    document_id=document.id,
                    document_title=document.title,
                    file_type=document.file_type,
                    kb_id=document.knowledge_base_id,
                )

                return []

            # 为每个文档添加知识库ID
            for doc in extracted_documents:
                doc.metadata["knowledge_base_id"] = document.knowledge_base_id
                doc.metadata["document_id"] = document.id
                doc.metadata["document_title"] = document.title
                doc.metadata["file_type"] = document.file_type

            # 计算提取统计
            total_content_length = sum(
                len(doc.page_content) for doc in extracted_documents
            )
            avg_content_length = (
                total_content_length / len(extracted_documents)
                if extracted_documents
                else 0
            )

            # 记录文档提取成功
            Logger.debug(f"文档提取完成:")
            Logger.debug(f"  - 提取文档数: {len(extracted_documents)}")
            Logger.debug(f"  - 总内容长度: {total_content_length}")
            Logger.debug(f"  - 平均内容长度: {avg_content_length:.1f}")
            Logger.debug(f"  - 处理耗时: {process_time:.3f}秒")

            # 记录成功的性能指标
            Logger.rag_performance_metrics(
                operation="document_extract_success",
                duration=process_time,
                document_id=document.id,
                document_title=document.title,
                file_type=document.file_type,
                kb_id=document.knowledge_base_id,
                extracted_document_count=len(extracted_documents),
                total_content_length=total_content_length,
                avg_content_length=avg_content_length,
                processing_speed=(
                    total_content_length / process_time if process_time > 0 else 0
                ),
            )

            return extracted_documents

        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time

            import traceback

            error_info = traceback.format_exc()

            Logger.error(f"提取文档内容失败:")
            Logger.error(f"  - 文档ID: {document.id}")
            Logger.error(f"  - 文档标题: {document.title}")
            Logger.error(f"  - 文档类型: {document.file_type}")
            Logger.error(f"  - 错误信息: {str(e)}")
            Logger.debug(f"堆栈跟踪:\n{error_info}")

            # 记录失败的性能指标
            Logger.rag_performance_metrics(
                operation="document_extract_failed",
                duration=process_time,
                document_id=document.id,
                document_title=document.title,
                file_type=document.file_type,
                kb_id=document.knowledge_base_id,
                error=str(e),
                error_type=type(e).__name__,
            )

            return []

    async def transform(self, documents: List[Document], **kwargs) -> List[Document]:
        """转换文档

        Args:
            documents: 文档对象列表
            **kwargs: 其他参数

        Returns:
            List[Document]: 转换后的文档对象列表
        """
        start_time = time.time()

        # 记录文档转换开始
        total_input_length = sum(len(doc.page_content) for doc in documents)
        Logger.debug(f"开始转换文档:")
        Logger.debug(f"  - 输入文档数: {len(documents)}")
        Logger.debug(f"  - 总输入长度: {total_input_length}")
        Logger.debug(f"  - 分块大小: {self.splitter._chunk_size}")
        Logger.debug(f"  - 分块重叠: {self.splitter._chunk_overlap}")

        try:
            transformed_documents = []
            cleaning_time = 0
            splitting_time = 0

            for doc_idx, doc in enumerate(documents):
                # 清理文本内容
                clean_start = time.time()
                cleaned_content = self.cleaner.clean(doc.page_content)
                cleaning_time += time.time() - clean_start

                # 分割文本
                split_start = time.time()
                chunks = self.splitter.split_text(cleaned_content)
                splitting_time += time.time() - split_start

                Logger.debug(
                    f"文档 {doc_idx + 1}/{len(documents)} 处理: 原长度 {len(doc.page_content)}, 清理后 {len(cleaned_content)}, 分块数 {len(chunks)}"
                )

                # 创建文档对象
                for i, chunk in enumerate(chunks):
                    # 生成唯一ID
                    doc_id = doc.metadata.get("doc_id") or str(uuid.uuid4())
                    chunk_id = f"{doc_id}_{i}"

                    # 创建文档对象
                    transformed_doc = Document(
                        page_content=chunk,
                        metadata={
                            **doc.metadata,
                            "doc_id": chunk_id,
                            "chunk_index": i,
                            "original_doc_id": doc_id,
                            "chunk_length": len(chunk),
                            "original_length": len(doc.page_content),
                            "cleaned_length": len(cleaned_content),
                        },
                    )
                    transformed_documents.append(transformed_doc)

            # 计算处理时间
            total_time = time.time() - start_time

            # 计算转换统计
            total_output_length = sum(
                len(doc.page_content) for doc in transformed_documents
            )
            avg_chunk_length = (
                total_output_length / len(transformed_documents)
                if transformed_documents
                else 0
            )
            expansion_ratio = (
                len(transformed_documents) / len(documents) if documents else 0
            )

            # 记录文档转换完成
            Logger.debug(f"文档转换完成:")
            Logger.debug(f"  - 输出文档数: {len(transformed_documents)}")
            Logger.debug(f"  - 总输出长度: {total_output_length}")
            Logger.debug(f"  - 平均分块长度: {avg_chunk_length:.1f}")
            Logger.debug(f"  - 扩展比例: {expansion_ratio:.2f}")
            Logger.debug(f"  - 清理耗时: {cleaning_time:.3f}秒")
            Logger.debug(f"  - 分块耗时: {splitting_time:.3f}秒")
            Logger.debug(f"  - 总耗时: {total_time:.3f}秒")

            # 记录成功的性能指标
            Logger.rag_performance_metrics(
                operation="document_transform_success",
                duration=total_time,
                input_document_count=len(documents),
                output_document_count=len(transformed_documents),
                total_input_length=total_input_length,
                total_output_length=total_output_length,
                avg_chunk_length=avg_chunk_length,
                expansion_ratio=expansion_ratio,
                cleaning_time=cleaning_time,
                splitting_time=splitting_time,
                chunk_size=self.splitter._chunk_size,
                chunk_overlap=self.splitter._chunk_overlap,
                processing_speed=(
                    total_input_length / total_time if total_time > 0 else 0
                ),
            )

            return transformed_documents

        except Exception as e:
            # 计算处理时间
            total_time = time.time() - start_time

            import traceback

            error_info = traceback.format_exc()

            Logger.error(f"转换文档失败:")
            Logger.error(f"  - 输入文档数: {len(documents)}")
            Logger.error(f"  - 总输入长度: {total_input_length}")
            Logger.error(f"  - 错误信息: {str(e)}")
            Logger.debug(f"堆栈跟踪:\n{error_info}")

            # 记录失败的性能指标
            Logger.rag_performance_metrics(
                operation="document_transform_failed",
                duration=total_time,
                input_document_count=len(documents),
                total_input_length=total_input_length,
                error=str(e),
                error_type=type(e).__name__,
            )

            return documents

    async def load(
        self, knowledge_base: KnowledgeBase, documents: List[Document], **kwargs
    ) -> None:
        """加载文档到索引

        Args:
            knowledge_base: 知识库对象
            documents: 文档对象列表
            **kwargs: 其他参数
        """
        start_time = time.time()

        # 记录索引构建开始
        total_content_length = sum(len(doc.page_content) for doc in documents)
        Logger.info(f"开始构建索引:")
        Logger.info(f"  - 知识库ID: {knowledge_base.id}")
        Logger.info(f"  - 知识库名称: {knowledge_base.name}")
        Logger.info(f"  - 文档数量: {len(documents)}")
        Logger.info(f"  - 总内容长度: {total_content_length}")
        Logger.info(
            f"  - 向量存储类型: {knowledge_base.vector_store_type or settings.RAG_VECTOR_STORE_TYPE}"
        )
        Logger.info(f"  - 嵌入模型: {knowledge_base.embedding_model}")

        # 记录索引构建开始的性能指标
        Logger.rag_performance_metrics(
            operation="index_build_start",
            duration=0.0,
            kb_id=knowledge_base.id,
            kb_name=knowledge_base.name,
            document_count=len(documents),
            total_content_length=total_content_length,
            vector_store_type=knowledge_base.vector_store_type
            or settings.RAG_VECTOR_STORE_TYPE,
            embedding_model=knowledge_base.embedding_model,
        )

        try:
            # 获取数据库会话
            db: Session = kwargs.get("db")
            if not db:
                raise ValueError("缺少数据库会话")

            # 获取LLM配置
            llm_config: LLMConfig = kwargs.get("llm_config")
            if not llm_config:
                raise ValueError("缺少LLM配置")

            # 创建向量化引擎
            embedding_start_time = time.time()
            embedding_engine = EmbeddingEngine(llm_config)

            # 向量化文档
            Logger.debug(f"开始向量化 {len(documents)} 个文档...")
            vectorized_documents = await embedding_engine.batch_embed_documents(
                documents
            )
            embedding_time = time.time() - embedding_start_time

            Logger.debug(f"向量化完成，耗时: {embedding_time:.2f}秒")

            # 创建向量存储
            vector_store_start_time = time.time()
            vector_store = VectorFactory.create_vector_store(knowledge_base, llm_config)

            # 添加到向量存储
            Logger.debug(f"开始添加向量到存储...")
            await vector_store.add_texts(
                vectorized_documents,
                [doc.vector for doc in vectorized_documents],
                duplicate_check=True,
            )
            vector_store_time = time.time() - vector_store_start_time

            Logger.debug(f"向量存储完成，耗时: {vector_store_time:.2f}秒")

            # 保存到数据库
            db_start_time = time.time()
            Logger.debug(f"开始保存到数据库...")

            chunk_count = 0
            embedding_count = 0

            for doc in vectorized_documents:
                # 创建文档分块
                chunk = DocumentChunk(
                    document_id=doc.metadata.get("document_id"),
                    content=doc.page_content,
                    chunk_index=doc.metadata.get("chunk_index", 0),
                    metadata=doc.metadata,
                )
                db.add(chunk)
                await db.flush()
                chunk_count += 1

                # 创建文档向量
                embedding = DocumentEmbedding(
                    chunk_id=chunk.id,
                    embedding=doc.vector,
                    model=knowledge_base.embedding_model,
                )
                db.add(embedding)
                embedding_count += 1

            # 提交事务
            await db.commit()
            db_time = time.time() - db_start_time

            Logger.debug(f"数据库保存完成，耗时: {db_time:.2f}秒")
            Logger.debug(f"  - 创建分块数: {chunk_count}")
            Logger.debug(f"  - 创建向量数: {embedding_count}")

            # 使缓存失效
            cache_start_time = time.time()
            document_id = (
                documents[0].metadata.get("document_id") if documents else None
            )
            if document_id:
                await IndexCache.invalidate_index(
                    kb_id=knowledge_base.id,
                    index_type="standard_retrieval",
                    document_id=int(document_id),
                )
                Logger.debug(f"使文档 {document_id} 的缓存失效")
            else:
                # 如果没有文档ID，使所有缓存失效
                await IndexCache.invalidate_all_indexes(knowledge_base.id)
                Logger.debug(f"使知识库 {knowledge_base.id} 的所有缓存失效")

            cache_time = time.time() - cache_start_time

            # 计算总处理时间
            total_time = time.time() - start_time

            # 记录索引构建完成
            Logger.info(f"索引构建完成:")
            Logger.info(f"  - 知识库ID: {knowledge_base.id}")
            Logger.info(f"  - 处理文档数: {len(vectorized_documents)}")
            Logger.info(f"  - 创建分块数: {chunk_count}")
            Logger.info(f"  - 创建向量数: {embedding_count}")
            Logger.info(f"  - 向量化耗时: {embedding_time:.2f}秒")
            Logger.info(f"  - 向量存储耗时: {vector_store_time:.2f}秒")
            Logger.info(f"  - 数据库保存耗时: {db_time:.2f}秒")
            Logger.info(f"  - 缓存清理耗时: {cache_time:.3f}秒")
            Logger.info(f"  - 总耗时: {total_time:.2f}秒")
            Logger.info(f"  - 处理速度: {len(documents)/total_time:.1f} 文档/秒")

            # 记录成功的性能指标
            Logger.rag_performance_metrics(
                operation="index_build_success",
                duration=total_time,
                kb_id=knowledge_base.id,
                kb_name=knowledge_base.name,
                document_count=len(documents),
                vectorized_document_count=len(vectorized_documents),
                chunk_count=chunk_count,
                embedding_count=embedding_count,
                total_content_length=total_content_length,
                embedding_time=embedding_time,
                vector_store_time=vector_store_time,
                database_time=db_time,
                cache_time=cache_time,
                processing_speed=len(documents) / total_time if total_time > 0 else 0,
                vector_store_type=knowledge_base.vector_store_type
                or settings.RAG_VECTOR_STORE_TYPE,
                embedding_model=knowledge_base.embedding_model,
            )

        except Exception as e:
            # 计算处理时间
            total_time = time.time() - start_time

            import traceback

            error_info = traceback.format_exc()

            Logger.error(f"加载文档到索引失败:")
            Logger.error(f"  - 知识库ID: {knowledge_base.id}")
            Logger.error(f"  - 文档数量: {len(documents)}")
            Logger.error(f"  - 已处理时间: {total_time:.2f}秒")
            Logger.error(f"  - 错误信息: {str(e)}")
            Logger.debug(f"堆栈跟踪:\n{error_info}")

            # 记录失败的性能指标
            Logger.rag_performance_metrics(
                operation="index_build_failed",
                duration=total_time,
                kb_id=knowledge_base.id,
                kb_name=knowledge_base.name,
                document_count=len(documents),
                total_content_length=total_content_length,
                error=str(e),
                error_type=type(e).__name__,
            )

            raise

    async def clean(
        self,
        knowledge_base: KnowledgeBase,
        document_ids: Optional[List[str]] = None,
        **kwargs,
    ) -> None:
        """清理索引

        Args:
            knowledge_base: 知识库对象
            document_ids: 文档ID列表，如果为None则清理整个索引
            **kwargs: 其他参数
        """
        start_time = time.time()

        # 记录索引清理开始
        if document_ids:
            Logger.info(f"开始清理指定文档的索引:")
            Logger.info(f"  - 知识库ID: {knowledge_base.id}")
            Logger.info(f"  - 知识库名称: {knowledge_base.name}")
            Logger.info(f"  - 文档ID列表: {document_ids}")
            Logger.info(f"  - 文档数量: {len(document_ids)}")
        else:
            Logger.info(f"开始清理整个知识库索引:")
            Logger.info(f"  - 知识库ID: {knowledge_base.id}")
            Logger.info(f"  - 知识库名称: {knowledge_base.name}")

        try:
            # 获取数据库会话
            db: Session = kwargs.get("db")
            if not db:
                raise ValueError("缺少数据库会话")

            # 获取LLM配置
            llm_config: LLMConfig = kwargs.get("llm_config")
            if not llm_config:
                raise ValueError("缺少LLM配置")

            # 创建向量存储
            vector_store_start_time = time.time()
            vector_store = VectorFactory.create_vector_store(knowledge_base, llm_config)

            deleted_chunks = 0
            deleted_embeddings = 0

            if document_ids:
                # 删除指定文档
                Logger.debug(f"开始从向量存储删除指定文档...")
                await vector_store.delete_by_ids(document_ids)
                vector_store_time = time.time() - vector_store_start_time

                # 从数据库中删除
                db_start_time = time.time()
                Logger.debug(f"开始从数据库删除相关记录...")

                chunks = await db.execute(
                    select(DocumentChunk).filter(
                        DocumentChunk.document_id.in_(document_ids)
                    )
                )
                for chunk in chunks.scalars().all():
                    await db.delete(chunk)
                    deleted_chunks += 1
                    # 删除分块时，相关的向量也会被级联删除
                    deleted_embeddings += 1

                db_time = time.time() - db_start_time

                # 使缓存失效
                cache_start_time = time.time()
                Logger.debug(f"开始清理相关缓存...")
                for doc_id in document_ids:
                    await IndexCache.invalidate_index(
                        kb_id=knowledge_base.id,
                        index_type="standard_retrieval",
                        document_id=int(doc_id),
                    )
                cache_time = time.time() - cache_start_time

                Logger.debug(f"指定文档索引清理完成:")
                Logger.debug(f"  - 删除文档数: {len(document_ids)}")
                Logger.debug(f"  - 删除分块数: {deleted_chunks}")
                Logger.debug(f"  - 删除向量数: {deleted_embeddings}")

            else:
                # 删除整个索引
                Logger.debug(f"开始删除整个向量存储...")
                await vector_store.delete()
                vector_store_time = time.time() - vector_store_start_time

                # 从数据库中删除
                db_start_time = time.time()
                Logger.debug(f"开始从数据库删除所有相关记录...")

                chunks = await db.execute(
                    select(DocumentChunk)
                    .join(DBDocument, DocumentChunk.document_id == DBDocument.id)
                    .filter(DBDocument.knowledge_base_id == knowledge_base.id)
                )
                for chunk in chunks.scalars().all():
                    await db.delete(chunk)
                    deleted_chunks += 1
                    deleted_embeddings += 1

                db_time = time.time() - db_start_time

                # 使所有缓存失效
                cache_start_time = time.time()
                Logger.debug(f"开始清理所有缓存...")
                await IndexCache.invalidate_all_indexes(knowledge_base.id)
                cache_time = time.time() - cache_start_time

                Logger.debug(f"整个索引清理完成:")
                Logger.debug(f"  - 删除分块数: {deleted_chunks}")
                Logger.debug(f"  - 删除向量数: {deleted_embeddings}")

            # 提交事务
            commit_start_time = time.time()
            await db.commit()
            commit_time = time.time() - commit_start_time

            # 计算总处理时间
            total_time = time.time() - start_time

            # 记录索引清理完成
            Logger.info(f"索引清理完成:")
            Logger.info(f"  - 知识库ID: {knowledge_base.id}")
            Logger.info(f"  - 清理类型: {'指定文档' if document_ids else '整个索引'}")
            Logger.info(f"  - 删除分块数: {deleted_chunks}")
            Logger.info(f"  - 删除向量数: {deleted_embeddings}")
            Logger.info(f"  - 向量存储清理耗时: {vector_store_time:.3f}秒")
            Logger.info(f"  - 数据库清理耗时: {db_time:.3f}秒")
            Logger.info(f"  - 缓存清理耗时: {cache_time:.3f}秒")
            Logger.info(f"  - 事务提交耗时: {commit_time:.3f}秒")
            Logger.info(f"  - 总耗时: {total_time:.3f}秒")

            # 记录成功的性能指标
            Logger.rag_performance_metrics(
                operation="index_clean_success",
                duration=total_time,
                kb_id=knowledge_base.id,
                kb_name=knowledge_base.name,
                clean_type="specific_documents" if document_ids else "full_index",
                document_count=len(document_ids) if document_ids else 0,
                deleted_chunks=deleted_chunks,
                deleted_embeddings=deleted_embeddings,
                vector_store_time=vector_store_time,
                database_time=db_time,
                cache_time=cache_time,
                commit_time=commit_time,
            )

        except Exception as e:
            # 计算处理时间
            total_time = time.time() - start_time

            import traceback

            error_info = traceback.format_exc()

            Logger.error(f"清理索引失败:")
            Logger.error(f"  - 知识库ID: {knowledge_base.id}")
            Logger.error(f"  - 清理类型: {'指定文档' if document_ids else '整个索引'}")
            Logger.error(f"  - 已处理时间: {total_time:.3f}秒")
            Logger.error(f"  - 错误信息: {str(e)}")
            Logger.debug(f"堆栈跟踪:\n{error_info}")

            # 记录失败的性能指标
            Logger.rag_performance_metrics(
                operation="index_clean_failed",
                duration=total_time,
                kb_id=knowledge_base.id,
                kb_name=knowledge_base.name,
                clean_type="specific_documents" if document_ids else "full_index",
                document_count=len(document_ids) if document_ids else 0,
                error=str(e),
                error_type=type(e).__name__,
            )

            raise

    async def retrieve(
        self, knowledge_base: KnowledgeBase, query: str, top_k: int = 5, **kwargs
    ) -> List[Document]:
        """检索文档

        Args:
            knowledge_base: 知识库对象
            query: 查询文本
            top_k: 返回结果数量
            **kwargs: 其他参数

        Returns:
            List[Document]: 检索结果
        """
        start_time = time.time()

        # 记录检索开始
        query_preview = query[:100] + "..." if len(query) > 100 else query
        Logger.debug(f"开始检索文档:")
        Logger.debug(f"  - 知识库ID: {knowledge_base.id}")
        Logger.debug(f"  - 知识库名称: {knowledge_base.name}")
        Logger.debug(f"  - 查询: '{query_preview}'")
        Logger.debug(f"  - 查询长度: {len(query)}")
        Logger.debug(f"  - 返回数量: {top_k}")

        try:
            # 检查是否使用缓存
            use_cache = kwargs.get("use_cache", True)

            # 生成缓存键
            cache_key = f"{query}_{top_k}"
            cache_hit = False

            # 检查缓存
            cache_check_start_time = time.time()
            if use_cache:
                cached_results = await IndexCache.get_cached_index(
                    kb_id=knowledge_base.id,
                    index_type="standard_retrieval",
                    document_id=hash(cache_key),
                )

                if cached_results:
                    cache_hit = True
                    cache_check_time = time.time() - cache_check_start_time

                    Logger.debug(f"缓存命中，返回缓存结果")
                    Logger.debug(f"  - 缓存检查耗时: {cache_check_time:.3f}秒")

                    # 反序列化文档
                    documents = []
                    for doc_data in cached_results["documents"]:
                        doc = Document(
                            page_content=doc_data["page_content"],
                            metadata=doc_data["metadata"],
                        )
                        if "vector" in doc_data:
                            doc.vector = doc_data["vector"]
                        documents.append(doc)

                    # 计算总时间
                    total_time = time.time() - start_time

                    # 记录缓存命中的性能指标
                    Logger.rag_performance_metrics(
                        operation="index_retrieve_cache_hit",
                        duration=total_time,
                        kb_id=knowledge_base.id,
                        kb_name=knowledge_base.name,
                        query_length=len(query),
                        top_k=top_k,
                        result_count=len(documents),
                        cache_check_time=cache_check_time,
                    )

                    return documents

            cache_check_time = time.time() - cache_check_start_time
            Logger.debug(f"缓存未命中，执行实际检索")
            Logger.debug(f"  - 缓存检查耗时: {cache_check_time:.3f}秒")

            # 获取LLM配置
            llm_config: LLMConfig = kwargs.get("llm_config")
            if not llm_config:
                raise ValueError("缺少LLM配置")

            # 创建向量化引擎
            embedding_start_time = time.time()
            embedding_engine = EmbeddingEngine(llm_config)

            # 向量化查询
            Logger.debug(f"开始向量化查询...")
            query_vector = await embedding_engine.embed_query(query)
            embedding_time = time.time() - embedding_start_time

            Logger.debug(f"查询向量化完成，耗时: {embedding_time:.3f}秒")

            # 创建向量存储
            vector_store_start_time = time.time()
            vector_store = VectorFactory.create_vector_store(knowledge_base, llm_config)

            # 执行检索
            Logger.debug(f"开始向量检索...")
            results = await vector_store.search_by_vector(
                query_vector, top_k=top_k, **kwargs
            )
            vector_search_time = time.time() - vector_store_start_time

            Logger.debug(
                f"向量检索完成，耗时: {vector_search_time:.3f}秒，返回 {len(results)} 个结果"
            )

            # 缓存结果
            cache_store_time = 0
            if use_cache and results:
                cache_store_start_time = time.time()
                Logger.debug(f"开始缓存检索结果...")

                # 序列化文档
                doc_data = []
                for doc in results:
                    doc_dict = {
                        "page_content": doc.page_content,
                        "metadata": doc.metadata,
                    }
                    if doc.vector:
                        doc_dict["vector"] = doc.vector
                    doc_data.append(doc_dict)

                # 缓存
                await IndexCache.cache_index(
                    kb_id=knowledge_base.id,
                    index_type="standard_retrieval",
                    index_data={"documents": doc_data},
                    document_id=hash(cache_key),
                )

                cache_store_time = time.time() - cache_store_start_time
                Logger.debug(f"结果缓存完成，耗时: {cache_store_time:.3f}秒")

            # 计算总时间
            total_time = time.time() - start_time

            # 计算检索质量指标
            if results:
                # 获取相似度分数（如果有的话）
                scores = [doc.metadata.get("score", 0.0) for doc in results]
                avg_score = sum(scores) / len(scores) if scores else 0.0
                max_score = max(scores) if scores else 0.0
                min_score = min(scores) if scores else 0.0

                # 内容长度统计
                content_lengths = [len(doc.page_content) for doc in results]
                avg_content_length = sum(content_lengths) / len(content_lengths)
            else:
                avg_score = max_score = min_score = avg_content_length = 0.0

            # 记录检索完成
            Logger.debug(f"文档检索完成:")
            Logger.debug(f"  - 返回结果数: {len(results)}")
            Logger.debug(f"  - 平均相似度: {avg_score:.4f}")
            Logger.debug(f"  - 相似度范围: [{min_score:.4f}, {max_score:.4f}]")
            Logger.debug(f"  - 平均内容长度: {avg_content_length:.1f}")
            Logger.debug(f"  - 缓存检查耗时: {cache_check_time:.3f}秒")
            Logger.debug(f"  - 查询向量化耗时: {embedding_time:.3f}秒")
            Logger.debug(f"  - 向量检索耗时: {vector_search_time:.3f}秒")
            Logger.debug(f"  - 结果缓存耗时: {cache_store_time:.3f}秒")
            Logger.debug(f"  - 总耗时: {total_time:.3f}秒")

            # 记录成功的性能指标
            Logger.rag_performance_metrics(
                operation="index_retrieve_success",
                duration=total_time,
                kb_id=knowledge_base.id,
                kb_name=knowledge_base.name,
                query_length=len(query),
                top_k=top_k,
                result_count=len(results),
                cache_hit=cache_hit,
                cache_check_time=cache_check_time,
                embedding_time=embedding_time,
                vector_search_time=vector_search_time,
                cache_store_time=cache_store_time,
                avg_score=avg_score,
                max_score=max_score,
                min_score=min_score,
                avg_content_length=avg_content_length,
            )

            return results

        except Exception as e:
            # 计算处理时间
            total_time = time.time() - start_time

            import traceback

            error_info = traceback.format_exc()

            Logger.error(f"检索文档失败:")
            Logger.error(f"  - 知识库ID: {knowledge_base.id}")
            Logger.error(f"  - 查询: '{query_preview}'")
            Logger.error(f"  - 查询长度: {len(query)}")
            Logger.error(f"  - 返回数量: {top_k}")
            Logger.error(f"  - 已处理时间: {total_time:.3f}秒")
            Logger.error(f"  - 错误信息: {str(e)}")
            Logger.debug(f"堆栈跟踪:\n{error_info}")

            # 记录失败的性能指标
            Logger.rag_performance_metrics(
                operation="index_retrieve_failed",
                duration=total_time,
                kb_id=knowledge_base.id,
                kb_name=knowledge_base.name,
                query_length=len(query),
                top_k=top_k,
                error=str(e),
                error_type=type(e).__name__,
            )

            return []
