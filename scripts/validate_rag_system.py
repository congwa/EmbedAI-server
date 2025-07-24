#!/usr/bin/env python3
"""
RAG系统功能验证脚本

这个脚本会验证RAG知识库训练功能的所有核心组件，
确保系统能够正常工作。

使用方法:
    python scripts/validate_rag_system.py
"""

import asyncio
import os
import sys
import time
import tempfile
import statistics
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import Settings
from app.core.database import get_db
from app.core.redis import redis_manager
from app.services.knowledge_base import KnowledgeBaseService
from app.models.llm_config import LLMConfig
from app.rag.embedding.embedding_engine import EmbeddingEngine
from app.rag.datasource.vdb.vector_factory import VectorStoreFactory
from app.rag.retrieval.query_cache import QueryCache
from app.rag.index_processor.index_cache import IndexCache


class RAGSystemValidator:
    """RAG系统验证器"""
    
    def __init__(self):
        self.settings = Settings()
        self.db = next(get_db())
        self.kb_service = KnowledgeBaseService(self.db)
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, message: str = "", details: Dict = None):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "details": details or {},
            "timestamp": time.time()
        }
        self.test_results.append(result)
        
        status = "✓" if success else "✗"
        print(f"{status} {test_name}: {message}")
        
        if details:
            for key, value in details.items():
                print(f"    {key}: {value}")
    
    async def validate_environment(self) -> bool:
        """验证环境配置"""
        print("\n=== 环境配置验证 ===")
        
        try:
            # 验证配置加载
            required_configs = [
                "VECTOR_DB_TYPE", "RAG_CHUNK_SIZE", "RAG_EMBEDDING_BATCH_SIZE"
            ]
            
            missing_configs = []
            for config in required_configs:
                if not hasattr(self.settings, config):
                    missing_configs.append(config)
            
            if missing_configs:
                self.log_result(
                    "配置验证", False, 
                    f"缺少必需配置: {', '.join(missing_configs)}"
                )
                return False
            
            self.log_result(
                "配置验证", True, "所有必需配置已加载",
                {
                    "向量数据库类型": self.settings.VECTOR_DB_TYPE,
                    "分块大小": self.settings.RAG_CHUNK_SIZE,
                    "批处理大小": self.settings.RAG_EMBEDDING_BATCH_SIZE
                }
            )
            
            # 验证数据库连接
            try:
                # 简单查询测试数据库连接
                self.db.execute("SELECT 1")
                self.log_result("数据库连接", True, "数据库连接正常")
            except Exception as e:
                self.log_result("数据库连接", False, f"数据库连接失败: {e}")
                return False
            
            # 验证Redis连接
            try:
                await redis_manager.ping()
                self.log_result("Redis连接", True, "Redis连接正常")
            except Exception as e:
                self.log_result("Redis连接", False, f"Redis连接失败: {e}")
                return False
            
            # 验证向量数据库
            try:
                vector_store = VectorStoreFactory.create_vector_store(
                    self.settings.VECTOR_DB_TYPE, {}
                )
                self.log_result("向量数据库", True, "向量数据库初始化成功")
            except Exception as e:
                self.log_result("向量数据库", False, f"向量数据库初始化失败: {e}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("环境验证", False, f"环境验证异常: {e}")
            return False
    
    async def validate_document_processing(self) -> bool:
        """验证文档处理功能"""
        print("\n=== 文档处理验证 ===")
        
        try:
            from app.rag.extractor.extract_processor import ExtractProcessor
            from app.rag.splitter.text_splitter import TextSplitter
            
            # 创建测试文档
            test_content = """# 测试文档

## 概述
这是一个用于测试RAG功能的示例文档。

## 功能特性
- 文档解析和处理
- 智能分块
- 向量化存储
- 语义搜索

## 技术架构
系统采用微服务架构，包含以下组件：
1. 文档处理服务
2. 向量化服务
3. 检索服务
4. 缓存服务

## 使用方法
1. 上传文档到知识库
2. 进行RAG训练
3. 执行智能查询

这个文档包含了足够的内容来测试文本分块功能。
"""
            
            # 测试文档提取
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                f.write(test_content)
                temp_file = f.name
            
            try:
                processor = ExtractProcessor()
                extracted_content = await processor.extract_from_file(temp_file)
                
                if extracted_content and len(extracted_content.strip()) > 0:
                    self.log_result(
                        "文档提取", True, "文档内容提取成功",
                        {"提取内容长度": len(extracted_content)}
                    )
                else:
                    self.log_result("文档提取", False, "提取的内容为空")
                    return False
                
                # 测试文本分块
                splitter = TextSplitter(
                    chunk_size=200,
                    chunk_overlap=50,
                    strategy="recursive_character"
                )
                
                chunks = await splitter.split_text(extracted_content)
                
                if chunks and len(chunks) > 0:
                    self.log_result(
                        "文本分块", True, "文本分块成功",
                        {
                            "分块数量": len(chunks),
                            "平均分块长度": sum(len(chunk) for chunk in chunks) // len(chunks)
                        }
                    )
                else:
                    self.log_result("文本分块", False, "文本分块失败")
                    return False
                
            finally:
                os.unlink(temp_file)
            
            return True
            
        except Exception as e:
            self.log_result("文档处理", False, f"文档处理验证异常: {e}")
            return False
    
    async def validate_embedding(self) -> bool:
        """验证向量化功能"""
        print("\n=== 向量化功能验证 ===")
        
        try:
            # 创建测试LLM配置
            llm_config = LLMConfig(
                embeddings={
                    "provider": "openai",
                    "model": "text-embedding-ada-002",
                    "api_key": "your-api-key",
                    "batch_size": 10
                }
            )
            
            engine = EmbeddingEngine(llm_config)
            
            # 测试单个文本向量化
            test_text = "这是一个测试文本，用于验证向量化功能。"
            embedding = await engine.embed_query(test_text)
            
            if embedding and len(embedding) > 0:
                self.log_result(
                    "单文本向量化", True, "单文本向量化成功",
                    {
                        "向量维度": len(embedding),
                        "向量范数": f"{sum(x*x for x in embedding)**0.5:.4f}"
                    }
                )
            else:
                self.log_result("单文本向量化", False, "向量化结果为空")
                return False
            
            # 测试批量向量化
            test_texts = [
                "第一个测试文本",
                "第二个测试文本",
                "第三个测试文本"
            ]
            
            embeddings = await engine.embed_documents(test_texts)
            
            if embeddings and len(embeddings) == len(test_texts):
                self.log_result(
                    "批量向量化", True, "批量向量化成功",
                    {
                        "文本数量": len(test_texts),
                        "向量数量": len(embeddings),
                        "向量维度": len(embeddings[0]) if embeddings else 0
                    }
                )
            else:
                self.log_result("批量向量化", False, "批量向量化失败")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("向量化功能", False, f"向量化验证异常: {e}")
            return False
    
    async def validate_vector_storage(self) -> bool:
        """验证向量存储功能"""
        print("\n=== 向量存储验证 ===")
        
        try:
            # 创建向量存储实例
            vector_store = VectorStoreFactory.create_vector_store(
                self.settings.VECTOR_DB_TYPE,
                {"collection_name": "test_collection"}
            )
            
            # 准备测试数据
            test_texts = [
                "人工智能是计算机科学的一个分支",
                "机器学习是人工智能的子领域",
                "深度学习使用神经网络进行学习"
            ]
            
            test_embeddings = []
            for text in test_texts:
                # 创建简单的测试向量
                embedding = [float(i) for i in range(384)]  # 384维测试向量
                test_embeddings.append(embedding)
            
            # 测试向量存储
            try:
                await vector_store.add_texts(
                    texts=test_texts,
                    embeddings=test_embeddings,
                    metadatas=[{"source": f"test_{i}"} for i in range(len(test_texts))]
                )
                
                self.log_result(
                    "向量存储", True, "向量存储成功",
                    {"存储向量数量": len(test_texts)}
                )
            except Exception as e:
                self.log_result("向量存储", False, f"向量存储失败: {e}")
                return False
            
            # 测试向量检索
            try:
                query_embedding = test_embeddings[0]  # 使用第一个向量作为查询
                results = await vector_store.similarity_search_by_vector(
                    query_embedding, k=2
                )
                
                if results and len(results) > 0:
                    self.log_result(
                        "向量检索", True, "向量检索成功",
                        {"检索结果数量": len(results)}
                    )
                else:
                    self.log_result("向量检索", False, "检索结果为空")
                    return False
                    
            except Exception as e:
                self.log_result("向量检索", False, f"向量检索失败: {e}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("向量存储", False, f"向量存储验证异常: {e}")
            return False
    
    async def validate_knowledge_base_operations(self) -> bool:
        """验证知识库操作"""
        print("\n=== 知识库操作验证 ===")
        
        try:
            # 创建测试知识库
            kb = await self.kb_service.create_knowledge_base(
                name="测试知识库",
                description="用于系统验证的测试知识库",
                user_id=1
            )
            
            if not kb:
                self.log_result("知识库创建", False, "知识库创建失败")
                return False
            
            self.log_result(
                "知识库创建", True, "知识库创建成功",
                {"知识库ID": kb.id, "知识库名称": kb.name}
            )
            
            # 创建测试文档
            test_content = "这是一个测试文档，包含了用于验证RAG功能的内容。"
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(test_content)
                temp_file = f.name
            
            try:
                # 上传文档
                document = await self.kb_service.upload_document(
                    knowledge_base_id=kb.id,
                    file_path=temp_file,
                    title="测试文档",
                    user_id=1
                )
                
                if document:
                    self.log_result(
                        "文档上传", True, "文档上传成功",
                        {"文档ID": document.id, "文档标题": document.title}
                    )
                else:
                    self.log_result("文档上传", False, "文档上传失败")
                    return False
                
                # 创建简单的LLM配置用于测试
                llm_config = LLMConfig(
                    embeddings={
                        "provider": "openai",
                        "model": "text-embedding-ada-002",
                        "api_key": "your-api-key",
                        "device": "cpu"
                    }
                )
                
                # 测试训练（简化版本，不执行完整训练）
                try:
                    training_status = await self.kb_service.get_training_status(kb.id)
                    self.log_result(
                        "训练状态查询", True, "训练状态查询成功",
                        {"状态": training_status.get("status", "unknown")}
                    )
                except Exception as e:
                    self.log_result("训练状态查询", False, f"训练状态查询失败: {e}")
                
            finally:
                os.unlink(temp_file)
            
            # 清理测试数据
            try:
                await self.kb_service.delete_knowledge_base(kb.id, user_id=1)
                self.log_result("知识库清理", True, "测试数据清理成功")
            except Exception as e:
                self.log_result("知识库清理", False, f"测试数据清理失败: {e}")
            
            return True
            
        except Exception as e:
            self.log_result("知识库操作", False, f"知识库操作验证异常: {e}")
            return False
    
    async def validate_caching(self) -> bool:
        """验证缓存功能"""
        print("\n=== 缓存功能验证 ===")
        
        try:
            # 测试查询缓存
            test_key = "test_query_cache"
            test_value = {"test": "data", "timestamp": time.time()}
            
            # 设置缓存
            await QueryCache.cache_result(
                kb_id=1,
                query="测试查询",
                method="semantic_search",
                top_k=5,
                use_rerank=False,
                rerank_mode=None,
                results=test_value
            )
            
            # 获取缓存
            cached_result = await QueryCache.get_cached_result(
                kb_id=1,
                query="测试查询",
                method="semantic_search",
                top_k=5,
                use_rerank=False,
                rerank_mode=None
            )
            
            if cached_result:
                self.log_result("查询缓存", True, "查询缓存功能正常")
            else:
                self.log_result("查询缓存", False, "查询缓存功能异常")
                return False
            
            # 测试缓存清理
            await QueryCache.clear_cache(kb_id=1)
            self.log_result("缓存清理", True, "缓存清理功能正常")
            
            return True
            
        except Exception as e:
            self.log_result("缓存功能", False, f"缓存验证异常: {e}")
            return False
    
    async def validate_performance(self) -> bool:
        """验证性能指标"""
        print("\n=== 性能验证 ===")
        
        try:
            # 测试向量化性能
            llm_config = LLMConfig(
                embeddings={
                    "provider": "openai",
                    "model": "text-embedding-ada-002",
                    "api_key": "your-api-key",
                    "batch_size": 10
                }
            )
            
            engine = EmbeddingEngine(llm_config)
            
            # 单次向量化性能测试
            test_text = "性能测试文本" * 50  # 创建较长的文本
            
            start_time = time.time()
            embedding = await engine.embed_query(test_text)
            single_time = time.time() - start_time
            
            # 批量向量化性能测试
            test_texts = [f"批量测试文本 {i}" for i in range(10)]
            
            start_time = time.time()
            embeddings = await engine.embed_documents(test_texts)
            batch_time = time.time() - start_time
            
            self.log_result(
                "向量化性能", True, "性能测试完成",
                {
                    "单次向量化时间": f"{single_time:.3f}s",
                    "批量向量化时间": f"{batch_time:.3f}s",
                    "批量平均时间": f"{batch_time/len(test_texts):.3f}s/个"
                }
            )
            
            # 性能评估
            if single_time < 5.0 and batch_time < 10.0:
                self.log_result("性能评估", True, "性能表现良好")
            else:
                self.log_result("性能评估", False, "性能需要优化")
            
            return True
            
        except Exception as e:
            self.log_result("性能验证", False, f"性能验证异常: {e}")
            return False
    
    def generate_report(self) -> Dict[str, Any]:
        """生成验证报告"""
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - successful_tests
        
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "success_rate": f"{success_rate:.1f}%"
            },
            "test_results": self.test_results,
            "recommendations": []
        }
        
        # 生成建议
        if failed_tests > 0:
            failed_test_names = [r["test_name"] for r in self.test_results if not r["success"]]
            report["recommendations"].append(
                f"以下测试失败，需要检查: {', '.join(failed_test_names)}"
            )
        
        if success_rate < 80:
            report["recommendations"].append("系统整体健康度较低，建议进行全面检查")
        elif success_rate < 95:
            report["recommendations"].append("系统基本正常，但有部分功能需要优化")
        else:
            report["recommendations"].append("系统运行状态良好")
        
        return report
    
    async def run_all_validations(self) -> bool:
        """运行所有验证测试"""
        print("开始RAG系统功能验证...")
        print("=" * 50)
        
        validation_steps = [
            ("环境配置", self.validate_environment),
            ("文档处理", self.validate_document_processing),
            ("向量化功能", self.validate_embedding),
            ("向量存储", self.validate_vector_storage),
            ("知识库操作", self.validate_knowledge_base_operations),
            ("缓存功能", self.validate_caching),
            ("性能指标", self.validate_performance)
        ]
        
        overall_success = True
        
        for step_name, validation_func in validation_steps:
            try:
                success = await validation_func()
                if not success:
                    overall_success = False
            except Exception as e:
                self.log_result(step_name, False, f"验证过程异常: {e}")
                overall_success = False
        
        # 生成报告
        report = self.generate_report()
        
        print("\n" + "=" * 50)
        print("验证报告")
        print("=" * 50)
        print(f"总测试数: {report['summary']['total_tests']}")
        print(f"成功测试: {report['summary']['successful_tests']}")
        print(f"失败测试: {report['summary']['failed_tests']}")
        print(f"成功率: {report['summary']['success_rate']}")
        
        if report["recommendations"]:
            print("\n建议:")
            for rec in report["recommendations"]:
                print(f"- {rec}")
        
        print("\n" + "=" * 50)
        if overall_success:
            print("✓ RAG系统验证通过，所有功能正常")
        else:
            print("✗ RAG系统验证失败，请检查失败的测试项")
        
        return overall_success


async def main():
    """主函数"""
    validator = RAGSystemValidator()
    
    try:
        success = await validator.run_all_validations()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n验证被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n验证过程发生异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())