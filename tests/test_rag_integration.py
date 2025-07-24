"""RAG功能集成测试"""
import pytest
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from main import app
from app.models.database import AsyncSessionLocal, engine, Base
from app.models.knowledge_base import PermissionType, TrainingStatus
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.document_embedding import DocumentEmbedding
from app.rag.training.training_manager import RAGTrainingManager
from app.rag.retrieval.retrieval_service import RetrievalService
from app.rag.retrieval.retrieval_methods import RetrievalMethod
from app.rag.rerank.rerank_type import RerankMode
from app.schemas.llm import LLMConfig
from app.schemas.identity import UserContext, UserType
from .utils.test_state import TestState
from tests.utils.decorators import step_decorator
import pytest_asyncio
import asyncio
from tests.base.base_test import BaseTest
from tests.base.auth_steps import (
    step_create_admin,
    step_admin_login,
    step_create_normal_user,
    step_user_login
)
from tests.base.knowledge_base_steps import (
    step_create_knowledge_base,
    step_get_kb_members
)
from tests.base.document_steps import step_create_document


class TestRAGIntegration(BaseTest):
    """RAG功能集成测试"""
    
    def get_test_name(self) -> str:
        return "rag_integration"
    
    @pytest.mark.asyncio
    async def test_full_flow(self, state, client):
        """完整的RAG测试流程"""
        # 用户认证流程
        await self.run_step(step_create_admin, state, client)
        await self.run_step(step_admin_login, state, client)
        await self.run_step(step_create_normal_user, state, client)
        await self.run_step(step_user_login, state, client)
        
        # 知识库管理流程
        await self.run_step(step_create_knowledge_base, state, client)
        await self.run_step(step_get_kb_members, state, client)
        
        # 文档管理
        await self.run_step(step_create_document, state, client)
        
        # RAG功能测试
        await self.run_step(self.step_test_document_processing, state, client)
        await self.run_step(self.step_test_embedding_generation, state, client)
        await self.run_step(self.step_test_rag_training, state, client)
        await self.run_step(self.step_test_rag_query, state, client)
        await self.run_step(self.step_test_rerank, state, client)
    
    @step_decorator("test_document_processing")
    async def step_test_document_processing(self, state, client):
        """测试文档处理功能"""
        kb_id = state.get_step_data("kb_id")
        
        async with AsyncSessionLocal() as db:
            # 获取文档
            result = await db.execute(
                f"SELECT * FROM documents WHERE knowledge_base_id = {kb_id}"
            )
            documents = result.fetchall()
            assert len(documents) > 0
            
            # 创建文档处理器
            from app.rag.extractor.extract_processor import ExtractProcessor
            from app.rag.splitter.text_splitter import TextSplitter
            
            extractor = ExtractProcessor()
            splitter = TextSplitter(chunk_size=100, chunk_overlap=20)
            
            # 处理第一个文档
            document = documents[0]
            
            # 模拟文档内容
            content = "这是一个测试文档，用于测试RAG功能。这个文档包含多个段落，用于测试文本分块功能。"
            content += "第二段落包含更多的文本内容，确保分块功能正常工作。"
            content += "第三段落添加更多的文本，以便生成多个文本块。这样可以测试向量化和检索功能。"
            
            # 分块文本
            chunks = splitter.split_text(content)
            
            # 验证分块结果
            assert len(chunks) > 0
            assert all(len(chunk) <= 100 for chunk in chunks)
            
            # 创建文档分块
            for i, chunk_text in enumerate(chunks):
                chunk = DocumentChunk(
                    document_id=document.id,
                    content=chunk_text,
                    chunk_index=i,
                    metadata={}
                )
                db.add(chunk)
            
            await db.commit()
            
            # 验证分块已保存
            result = await db.execute(
                f"SELECT * FROM document_chunks WHERE document_id = {document.id}"
            )
            db_chunks = result.fetchall()
            assert len(db_chunks) == len(chunks)
            
        return {"document_id": document.id, "chunk_count": len(chunks)}
    
    @step_decorator("test_embedding_generation")
    async def step_test_embedding_generation(self, state, client):
        """测试向量生成功能"""
        document_id = state.get_step_data("test_document_processing")["document_id"]
        
        async with AsyncSessionLocal() as db:
            # 获取文档分块
            result = await db.execute(
                f"SELECT * FROM document_chunks WHERE document_id = {document_id}"
            )
            chunks = result.fetchall()
            assert len(chunks) > 0
            
            # 创建向量引擎
            from app.rag.embedding.embedding_engine import EmbeddingEngine
            from app.core.config import settings
            
            embedding_engine = EmbeddingEngine(settings.DEFAULT_LLM_CONFIG)
            
            # 生成向量（模拟）
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = []
            for _ in chunk_texts:
                # 生成模拟向量（实际测试中应该调用真实的向量化API）
                import random
                vector = [random.random() for _ in range(10)]
                embeddings.append(vector)
            
            # 存储向量
            for chunk, embedding in zip(chunks, embeddings):
                doc_embedding = DocumentEmbedding(
                    chunk_id=chunk.id,
                    embedding=embedding,
                    model="test-model"
                )
                db.add(doc_embedding)
            
            await db.commit()
            
            # 验证向量已保存
            result = await db.execute(
                f"SELECT * FROM document_embeddings"
            )
            db_embeddings = result.fetchall()
            assert len(db_embeddings) == len(chunks)
            
        return {"document_id": document_id, "embedding_count": len(embeddings)}
    
    @step_decorator("test_rag_training")
    async def step_test_rag_training(self, state, client):
        """测试RAG训练功能"""
        kb_id = state.get_step_data("kb_id")
        user_token = state.get_step_data("user_token")
        
        # 开始训练
        response = client.post(
            f"/api/v1/admin/knowledge-bases/{kb_id}/train",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        
        # 验证训练状态
        async with AsyncSessionLocal() as db:
            # 创建训练管理器
            training_manager = RAGTrainingManager(db)
            
            # 模拟训练过程
            await training_manager.update_training_status(kb_id, TrainingStatus.TRAINING)
            
            # 验证状态已更新
            result = await db.execute(
                f"SELECT * FROM knowledge_bases WHERE id = {kb_id}"
            )
            kb = result.fetchone()
            assert kb.training_status == TrainingStatus.TRAINING
            
            # 模拟训练完成
            await training_manager.update_training_status(kb_id, TrainingStatus.TRAINED)
            
            # 验证状态已更新
            result = await db.execute(
                f"SELECT * FROM knowledge_bases WHERE id = {kb_id}"
            )
            kb = result.fetchone()
            assert kb.training_status == TrainingStatus.TRAINED
            
        return {"kb_id": kb_id, "training_status": "trained"}
    
    @step_decorator("test_rag_query")
    async def step_test_rag_query(self, state, client):
        """测试RAG查询功能"""
        kb_id = state.get_step_data("kb_id")
        user_token = state.get_step_data("user_token")
        
        # 创建用户上下文
        user_context = UserContext(
            user_type=UserType.OFFICIAL,
            user_id=state.get_step_data("user_id"),
            identity_id=None,
            client_id=None
        )
        
        async with AsyncSessionLocal() as db:
            # 创建检索服务
            retrieval_service = RetrievalService(db)
            
            # 获取知识库
            result = await db.execute(
                f"SELECT * FROM knowledge_bases WHERE id = {kb_id}"
            )
            kb = result.fetchone()
            
            # 创建LLM配置
            llm_config = LLMConfig.model_validate(kb.llm_config)
            
            # 执行查询（模拟）
            query = "测试查询"
            results = await retrieval_service.query(
                knowledge_base=kb,
                query=query,
                llm_config=llm_config,
                method=RetrievalMethod.SEMANTIC_SEARCH,
                top_k=3
            )
            
            # 验证结果
            assert isinstance(results, list)
            
        return {"kb_id": kb_id, "query": query}
    
    @step_decorator("test_rerank")
    async def step_test_rerank(self, state, client):
        """测试重排序功能"""
        kb_id = state.get_step_data("kb_id")
        user_token = state.get_step_data("user_token")
        
        # 创建用户上下文
        user_context = UserContext(
            user_type=UserType.OFFICIAL,
            user_id=state.get_step_data("user_id"),
            identity_id=None,
            client_id=None
        )
        
        async with AsyncSessionLocal() as db:
            # 创建检索服务
            retrieval_service = RetrievalService(db)
            
            # 获取知识库
            result = await db.execute(
                f"SELECT * FROM knowledge_bases WHERE id = {kb_id}"
            )
            kb = result.fetchone()
            
            # 创建LLM配置
            llm_config = LLMConfig.model_validate(kb.llm_config)
            
            # 执行查询（模拟）
            query = "测试查询"
            results = await retrieval_service.query(
                knowledge_base=kb,
                query=query,
                llm_config=llm_config,
                method=RetrievalMethod.HYBRID_SEARCH,
                top_k=3,
                use_rerank=True,
                rerank_mode=RerankMode.WEIGHTED_SCORE,
                user_id=str(user_context.user_id)
            )
            
            # 验证结果
            assert isinstance(results, list)
            
        return {"kb_id": kb_id, "query": query, "rerank_mode": RerankMode.WEIGHTED_SCORE}