#!/usr/bin/env python3
"""
RAG系统快速验证脚本

这个脚本提供快速的系统健康检查，适合日常使用。

使用方法:
    python scripts/quick_validation.py
"""

import asyncio
import os
import sys
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import Settings
from app.core.database import get_db
from app.core.redis import redis_manager
from app.rag.datasource.vdb.vector_factory import VectorStoreFactory


async def quick_health_check():
    """快速健康检查"""
    print("RAG系统快速健康检查")
    print("=" * 30)
    
    checks = []
    
    # 1. 配置检查
    try:
        settings = Settings()
        print("✓ 配置加载正常")
        checks.append(True)
    except Exception as e:
        print(f"✗ 配置加载失败: {e}")
        checks.append(False)
    
    # 2. 数据库检查
    try:
        db = next(get_db())
        db.execute("SELECT 1")
        print("✓ 数据库连接正常")
        checks.append(True)
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        checks.append(False)
    
    # 3. Redis检查
    try:
        await redis_manager.ping()
        print("✓ Redis连接正常")
        checks.append(True)
    except Exception as e:
        print(f"✗ Redis连接失败: {e}")
        checks.append(False)
    
    # 4. 向量数据库检查
    try:
        vector_store = VectorStoreFactory.create_vector_store(
            settings.VECTOR_DB_TYPE, {}
        )
        print("✓ 向量数据库正常")
        checks.append(True)
    except Exception as e:
        print(f"✗ 向量数据库异常: {e}")
        checks.append(False)
    
    # 5. 基础功能检查
    try:
        from app.rag.embedding.embedding_engine import EmbeddingEngine
        from app.models.llm_config import LLMConfig
        
        llm_config = LLMConfig(
            embeddings={
                "provider": "openai",
                "model": "text-embedding-ada-002",
                "api_key": "your-api-key"
            }
        )
        
        engine = EmbeddingEngine(llm_config)
        embedding = await engine.embed_query("测试")
        
        if embedding and len(embedding) > 0:
            print("✓ 向量化功能正常")
            checks.append(True)
        else:
            print("✗ 向量化功能异常")
            checks.append(False)
            
    except Exception as e:
        print(f"✗ 向量化功能异常: {e}")
        checks.append(False)
    
    # 总结
    success_count = sum(checks)
    total_count = len(checks)
    success_rate = (success_count / total_count * 100) if total_count > 0 else 0
    
    print("\n" + "=" * 30)
    print(f"检查结果: {success_count}/{total_count} ({success_rate:.1f}%)")
    
    if success_rate == 100:
        print("✓ 系统状态良好")
        return True
    elif success_rate >= 80:
        print("⚠ 系统基本正常，有部分问题")
        return True
    else:
        print("✗ 系统存在严重问题")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(quick_health_check())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n检查被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n检查过程异常: {e}")
        sys.exit(1)