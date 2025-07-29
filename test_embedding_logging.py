#!/usr/bin/env python3
"""测试向量化引擎日志功能"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.logger import Logger
from app.schemas.llm import LLMConfig, EmbeddingServiceConfig, LLMServiceConfig
from app.rag.embedding.embedding_engine import EmbeddingEngine

async def test_embedding_engine_logging():
    """测试向量化引擎的日志功能"""
    print("=== 测试向量化引擎日志功能 ===")
    
    # 初始化RAG追踪
    trace_id = Logger.init_rag_trace(
        kb_id=1,
        user_id=1,
        operation_type="training"
    )
    print(f"初始化RAG追踪: {trace_id}")
    
    # 创建LLM配置（使用模拟配置）
    llm_service_config = LLMServiceConfig(
        model="Qwen/Qwen2.5-7B-Instruct",
        base_url="https://api.siliconflow.cn/v1",
        api_key="test-key"
    )
    
    embedding_config = EmbeddingServiceConfig(
        model="BAAI/bge-m3",
        base_url="https://api.siliconflow.cn/v1",
        api_key="test-key",
        embedding_dim=1024
    )
    
    llm_config = LLMConfig(
        llm=llm_service_config,
        embeddings=embedding_config
    )
    
    # 创建向量化引擎
    embedding_engine = EmbeddingEngine(llm_config)
    
    # 测试文本
    test_texts = [
        "这是第一个测试文档，用于验证向量化引擎的日志功能。",
        "第二个文档包含了不同的内容，测试批量向量化的性能监控。",
        "最后一个文档用于测试向量质量评估和相似度计算功能。"
    ]
    
    test_query = "测试查询文本，用于验证查询向量化的日志记录。"
    
    try:
        print("\n--- 测试文档向量化 ---")
        # 这里会因为没有真实的API密钥而失败，但可以测试日志记录
        try:
            embeddings = await embedding_engine.embed_documents(test_texts)
            print(f"文档向量化成功，生成 {len(embeddings)} 个向量")
        except Exception as e:
            print(f"文档向量化失败（预期）: {e}")
        
        print("\n--- 测试查询向量化 ---")
        try:
            query_embedding = await embedding_engine.embed_query(test_query)
            print(f"查询向量化成功，向量维度: {len(query_embedding)}")
        except Exception as e:
            print(f"查询向量化失败（预期）: {e}")
        
        print("\n--- 测试批量向量化 ---")
        try:
            batch_embeddings = await embedding_engine.batch_embed_texts(test_texts, batch_size=2)
            print(f"批量向量化成功，生成 {len(batch_embeddings)} 个向量")
        except Exception as e:
            print(f"批量向量化失败（预期）: {e}")
        
        print("\n--- 测试相似度计算 ---")
        # 创建模拟向量进行相似度计算测试
        import numpy as np
        mock_query_vector = np.random.rand(1024).tolist()
        mock_doc_vectors = [np.random.rand(1024).tolist() for _ in range(3)]
        
        try:
            similarities = await embedding_engine.compute_similarity(mock_query_vector, mock_doc_vectors)
            print(f"相似度计算成功，计算了 {len(similarities)} 个相似度")
            print(f"相似度值: {[f'{sim:.4f}' for sim in similarities]}")
        except Exception as e:
            print(f"相似度计算失败: {e}")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

async def test_error_scenarios():
    """测试错误场景的日志记录"""
    print("\n=== 测试错误场景日志记录 ===")
    
    # 初始化RAG追踪
    trace_id = Logger.init_rag_trace(
        kb_id=2,
        user_id=1,
        operation_type="training"
    )
    print(f"初始化RAG追踪: {trace_id}")
    
    # 创建错误的配置
    llm_service_config = LLMServiceConfig(
        model="invalid-model",
        base_url="https://invalid-url.com",
        api_key="invalid-key"
    )
    
    embedding_config = EmbeddingServiceConfig(
        model="invalid-model",
        base_url="https://invalid-url.com",
        api_key="invalid-key",
        embedding_dim=0  # 无效维度
    )
    
    llm_config = LLMConfig(
        llm=llm_service_config,
        embeddings=embedding_config
    )
    
    # 创建向量化引擎
    embedding_engine = EmbeddingEngine(llm_config)
    
    # 测试空文本列表
    try:
        await embedding_engine.embed_documents([])
        print("空文本列表处理成功")
    except Exception as e:
        print(f"空文本列表处理失败: {e}")
    
    # 测试无效向量相似度计算
    try:
        await embedding_engine.compute_similarity([], [])
        print("无效向量相似度计算成功")
    except Exception as e:
        print(f"无效向量相似度计算失败: {e}")

async def main():
    """主函数"""
    print("开始测试向量化引擎日志功能...")
    
    await test_embedding_engine_logging()
    await test_error_scenarios()
    
    print("\n测试完成！请查看日志文件以验证日志记录功能。")

if __name__ == "__main__":
    asyncio.run(main())