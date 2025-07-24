# RAG知识库训练功能使用流程

## 概述

本文档提供了RAG（Retrieval-Augmented Generation）知识库训练功能的完整使用流程，包括从系统配置到实际使用的每个步骤，以及相应的代码验证方法。

## 完整使用流程

### 第一步：系统环境准备

#### 1.1 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt

# 安装向量数据库（选择其一）
# Chroma (推荐用于开发环境)
pip install chromadb

# Qdrant (推荐用于生产环境)
docker run -p 6333:6333 qdrant/qdrant
```

#### 1.2 配置环境变量

创建 `.env` 文件：

```bash
# 基础配置
VECTOR_DB_TYPE=chroma
CHROMA_PERSIST_DIRECTORY=./data/chroma_db

# LLM配置
OPENAI_API_KEY=your-openai-api-key
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379

# RAG配置
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=200
RAG_EMBEDDING_BATCH_SIZE=100
```

#### 1.3 验证环境配置

```python
# scripts/verify_environment.py
import asyncio
from app.core.config import Settings
from app.core.database import get_db
from app.core.redis import redis_manager

async def verify_environment():
    """验证环境配置"""
    print("=== 环境配置验证 ===")
    
    # 1. 验证配置加载
    try:
        settings = Settings()
        print("✓ 配置文件加载成功")
        print(f"  向量数据库类型: {settings.VECTOR_DB_TYPE}")
        print(f"  分块大小: {settings.RAG_CHUNK_SIZE}")
    except Exception as e:
        print(f"✗ 配置文件加载失败: {e}")
        return False
    
    # 2. 验证数据库连接
    try:
        db = next(get_db())
        print("✓ 数据库连接成功")
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        return False
    
    # 3. 验证Redis连接
    try:
        await redis_manager.ping()
        print("✓ Redis连接成功")
    except Exception as e:
        print(f"✗ Redis连接失败: {e}")
        return False
    
    # 4. 验证向量数据库
    try:
        from app.rag.datasource.vdb.vector_factory import VectorStoreFactory
        vector_store = VectorStoreFactory.create_vector_store(
            settings.VECTOR_DB_TYPE, {}
        )
        print("✓ 向量数据库初始化成功")
    except Exception as e:
        print(f"✗ 向量数据库初始化失败: {e}")
        return False
    
    print("\n环境验证完成！")
    return True

if __name__ == "__main__":
    asyncio.run(verify_environment())
```

### 第二步：创建知识库

#### 2.1 创建知识库

```python
# examples/create_knowledge_base.py
import asyncio
from app.services.knowledge_base import KnowledgeBaseService
from app.core.database import get_db

async def create_knowledge_base_example():
    """创建知识库示例"""
    print("=== 创建知识库 ===")
    
    # 获取数据库会话
    db = next(get_db())
    kb_service = KnowledgeBaseService(db)
    
    try:
        # 创建知识库
        knowledge_base = await kb_service.create_knowledge_base(
            name="技术文档知识库",
            description="用于存储和检索技术文档的知识库",
            user_id=1  # 替换为实际用户ID
        )
        
        print(f"✓ 知识库创建成功")
        print(f"  ID: {knowledge_base.id}")
        print(f"  名称: {knowledge_base.name}")
        print(f"  描述: {knowledge_base.description}")
        
        return knowledge_base
        
    except Exception as e:
        print(f"✗ 知识库创建失败: {e}")
        return None

if __name__ == "__main__":
    kb = asyncio.run(create_knowledge_base_example())
```

#### 2.2 验证知识库创建

```python
# 验证知识库是否创建成功
async def verify_knowledge_base(kb_id: int):
    """验证知识库"""
    db = next(get_db())
    kb_service = KnowledgeBaseService(db)
    
    try:
        kb = await kb_service.get_knowledge_base(kb_id)
        if kb:
            print(f"✓ 知识库验证成功: {kb.name}")
            return True
        else:
            print("✗ 知识库不存在")
            return False
    except Exception as e:
        print(f"✗ 知识库验证失败: {e}")
        return False
```

### 第三步：上传文档

#### 3.1 准备测试文档

```python
# examples/prepare_test_documents.py
import os

def create_test_documents():
    """创建测试文档"""
    test_dir = "./test_documents"
    os.makedirs(test_dir, exist_ok=True)
    
    # 创建Markdown测试文档
    md_content = """# 技术文档示例

## 概述
这是一个技术文档示例，用于测试RAG功能。

## 功能特性
- 文档解析和处理
- 智能分块
- 向量化存储
- 语义搜索

## 使用方法
1. 上传文档到知识库
2. 进行RAG训练
3. 执行智能查询

## 技术架构
系统采用微服务架构，包含以下组件：
- 文档处理服务
- 向量化服务
- 检索服务
- 缓存服务
"""
    
    with open(f"{test_dir}/tech_doc.md", "w", encoding="utf-8") as f:
        f.write(md_content)
    
    # 创建文本测试文档
    txt_content = """Python编程最佳实践

1. 代码风格
   - 遵循PEP 8规范
   - 使用有意义的变量名
   - 添加适当的注释

2. 错误处理
   - 使用try-except块
   - 记录详细的错误信息
   - 优雅地处理异常

3. 性能优化
   - 使用生成器处理大数据
   - 避免不必要的循环
   - 合理使用缓存

4. 测试
   - 编写单元测试
   - 使用pytest框架
   - 保持高测试覆盖率
"""
    
    with open(f"{test_dir}/python_best_practices.txt", "w", encoding="utf-8") as f:
        f.write(txt_content)
    
    print(f"✓ 测试文档创建完成，位置: {test_dir}")
    return [
        f"{test_dir}/tech_doc.md",
        f"{test_dir}/python_best_practices.txt"
    ]
```

#### 3.2 上传文档

```python
# examples/upload_documents.py
async def upload_documents_example(kb_id: int, file_paths: list):
    """上传文档示例"""
    print("=== 上传文档 ===")
    
    db = next(get_db())
    kb_service = KnowledgeBaseService(db)
    
    uploaded_documents = []
    
    for file_path in file_paths:
        try:
            # 上传文档
            document = await kb_service.upload_document(
                knowledge_base_id=kb_id,
                file_path=file_path,
                title=os.path.basename(file_path),
                user_id=1
            )
            
            uploaded_documents.append(document)
            print(f"✓ 文档上传成功: {document.title}")
            print(f"  ID: {document.id}")
            print(f"  大小: {document.file_size} bytes")
            
        except Exception as e:
            print(f"✗ 文档上传失败 {file_path}: {e}")
    
    return uploaded_documents

# 使用示例
file_paths = create_test_documents()
documents = await upload_documents_example(kb_id, file_paths)
```

#### 3.3 验证文档上传

```python
async def verify_documents(kb_id: int):
    """验证文档上传"""
    db = next(get_db())
    kb_service = KnowledgeBaseService(db)
    
    try:
        documents = await kb_service.get_documents(kb_id)
        print(f"✓ 知识库包含 {len(documents)} 个文档:")
        
        for doc in documents:
            print(f"  - {doc.title} (ID: {doc.id})")
            
        return len(documents) > 0
        
    except Exception as e:
        print(f"✗ 文档验证失败: {e}")
        return False
```

### 第四步：配置LLM

#### 4.1 创建LLM配置

```python
# examples/configure_llm.py
from app.models.llm_config import LLMConfig

def create_llm_config():
    """创建LLM配置"""
    print("=== 配置LLM ===")
    
    # OpenAI配置
    llm_config = LLMConfig(
        embeddings={
            "provider": "openai",
            "model": "text-embedding-ada-002",
            "api_key": os.getenv("OPENAI_API_KEY"),
            "batch_size": 100
        }
    )
    
    print("✓ LLM配置创建成功")
    print(f"  提供商: {llm_config.embeddings['provider']}")
    print(f"  模型: {llm_config.embeddings['model']}")
    
    return llm_config

# 本地模型配置示例
def create_local_llm_config():
    """创建本地LLM配置"""
    llm_config = LLMConfig(
        embeddings={
            "provider": "huggingface",
            "model": "sentence-transformers/all-MiniLM-L6-v2",
            "device": "cpu",
            "batch_size": 50
        }
    )
    
    return llm_config
```

#### 4.2 验证LLM配置

```python
async def verify_llm_config(llm_config: LLMConfig):
    """验证LLM配置"""
    print("=== 验证LLM配置 ===")
    
    try:
        from app.rag.embedding.embedding_engine import EmbeddingEngine
        
        # 创建向量化引擎
        engine = EmbeddingEngine(llm_config)
        
        # 测试向量化
        test_text = "这是一个测试文本"
        embedding = await engine.embed_query(test_text)
        
        print(f"✓ 向量化测试成功")
        print(f"  向量维度: {len(embedding)}")
        print(f"  向量范数: {sum(x*x for x in embedding)**0.5:.4f}")
        
        return True
        
    except Exception as e:
        print(f"✗ LLM配置验证失败: {e}")
        return False
```

### 第五步：执行RAG训练

#### 5.1 开始训练

```python
# examples/train_knowledge_base.py
async def train_knowledge_base_example(kb_id: int, llm_config: LLMConfig):
    """训练知识库示例"""
    print("=== 开始RAG训练 ===")
    
    db = next(get_db())
    kb_service = KnowledgeBaseService(db)
    
    try:
        # 开始训练
        training_result = await kb_service.train_rag(
            knowledge_base_id=kb_id,
            llm_config=llm_config,
            user_id=1
        )
        
        print(f"✓ 训练启动成功")
        print(f"  任务ID: {training_result.get('task_id')}")
        print(f"  状态: {training_result.get('status')}")
        
        return training_result
        
    except Exception as e:
        print(f"✗ 训练启动失败: {e}")
        return None

# 异步训练示例
async def train_async_example(kb_id: int, llm_config: LLMConfig):
    """异步训练示例"""
    from app.utils.tasks import train_rag_knowledge_base
    
    # 提交异步任务
    task = train_rag_knowledge_base.schedule(
        args=(kb_id, llm_config.dict(), 1),
        delay=0
    )
    
    print(f"✓ 异步训练任务已提交: {task.id}")
    return task
```

#### 5.2 监控训练进度

```python
async def monitor_training_progress(kb_id: int):
    """监控训练进度"""
    print("=== 监控训练进度 ===")
    
    db = next(get_db())
    kb_service = KnowledgeBaseService(db)
    
    import time
    
    while True:
        try:
            status = await kb_service.get_training_status(kb_id)
            
            print(f"训练状态: {status['status']}")
            print(f"进度: {status.get('progress', 0)}%")
            print(f"处理文档: {status.get('processed_documents', 0)}/{status.get('total_documents', 0)}")
            
            if status['status'] in ['completed', 'failed']:
                break
                
            time.sleep(5)  # 每5秒检查一次
            
        except Exception as e:
            print(f"获取训练状态失败: {e}")
            break
    
    print("训练监控结束")
```

#### 5.3 验证训练结果

```python
async def verify_training_result(kb_id: int):
    """验证训练结果"""
    print("=== 验证训练结果 ===")
    
    db = next(get_db())
    kb_service = KnowledgeBaseService(db)
    
    try:
        # 检查知识库状态
        kb = await kb_service.get_knowledge_base(kb_id)
        print(f"知识库状态: {kb.status}")
        
        # 检查文档分块
        from app.models.document_chunk import DocumentChunk
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id.in_(
                [doc.id for doc in kb.documents]
            )
        ).all()
        
        print(f"✓ 生成文档分块: {len(chunks)} 个")
        
        # 检查向量索引
        from app.rag.retrieval.retrieval_service import RetrievalService
        retrieval_service = RetrievalService(db)
        
        index_status = await retrieval_service.check_index_status(kb_id)
        print(f"✓ 向量索引状态: {'存在' if index_status['exists'] else '不存在'}")
        
        if index_status['exists']:
            print(f"  索引大小: {index_status.get('size', 'N/A')}")
            print(f"  向量数量: {index_status.get('vector_count', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"✗ 训练结果验证失败: {e}")
        return False
```

### 第六步：执行查询

#### 6.1 基础查询

```python
# examples/query_knowledge_base.py
async def query_knowledge_base_example(kb_id: int, llm_config: LLMConfig):
    """查询知识库示例"""
    print("=== 查询知识库 ===")
    
    db = next(get_db())
    kb_service = KnowledgeBaseService(db)
    
    # 测试查询列表
    test_queries = [
        "什么是RAG功能？",
        "如何进行文档处理？",
        "Python编程最佳实践有哪些？",
        "系统架构是什么样的？"
    ]
    
    for query in test_queries:
        print(f"\n查询: {query}")
        
        try:
            results = await kb_service.query_rag(
                knowledge_base_id=kb_id,
                query=query,
                llm_config=llm_config,
                method="semantic_search",
                top_k=3,
                user_id=1
            )
            
            print(f"✓ 找到 {len(results)} 个相关结果:")
            
            for i, result in enumerate(results, 1):
                print(f"  {i}. 相关度: {result.get('score', 0):.4f}")
                print(f"     内容: {result['content'][:100]}...")
                print(f"     来源: {result.get('document', {}).get('title', 'Unknown')}")
                
        except Exception as e:
            print(f"✗ 查询失败: {e}")

# 使用示例
await query_knowledge_base_example(kb_id, llm_config)
```

#### 6.2 高级查询

```python
async def advanced_query_example(kb_id: int, llm_config: LLMConfig):
    """高级查询示例"""
    print("=== 高级查询示例 ===")
    
    db = next(get_db())
    kb_service = KnowledgeBaseService(db)
    
    query = "Python编程规范"
    
    # 1. 语义搜索
    print("\n1. 语义搜索:")
    semantic_results = await kb_service.query_rag(
        knowledge_base_id=kb_id,
        query=query,
        llm_config=llm_config,
        method="semantic_search",
        top_k=5
    )
    print(f"语义搜索结果: {len(semantic_results)} 个")
    
    # 2. 关键词搜索
    print("\n2. 关键词搜索:")
    keyword_results = await kb_service.query_rag(
        knowledge_base_id=kb_id,
        query=query,
        llm_config=llm_config,
        method="keyword_search",
        top_k=5
    )
    print(f"关键词搜索结果: {len(keyword_results)} 个")
    
    # 3. 混合搜索
    print("\n3. 混合搜索:")
    hybrid_results = await kb_service.query_rag(
        knowledge_base_id=kb_id,
        query=query,
        llm_config=llm_config,
        method="hybrid_search",
        top_k=5,
        semantic_weight=0.7,
        keyword_weight=0.3
    )
    print(f"混合搜索结果: {len(hybrid_results)} 个")
    
    # 4. 带重排序的搜索
    print("\n4. 带重排序的搜索:")
    rerank_results = await kb_service.query_rag(
        knowledge_base_id=kb_id,
        query=query,
        llm_config=llm_config,
        method="semantic_search",
        top_k=10,
        use_rerank=True,
        rerank_mode="weighted_score"
    )
    print(f"重排序搜索结果: {len(rerank_results)} 个")
```

#### 6.3 验证查询结果

```python
async def verify_query_results(results: list, expected_keywords: list):
    """验证查询结果"""
    print("=== 验证查询结果 ===")
    
    if not results:
        print("✗ 查询无结果")
        return False
    
    # 检查结果数量
    print(f"✓ 返回结果数量: {len(results)}")
    
    # 检查结果格式
    for i, result in enumerate(results):
        required_fields = ['content', 'score']
        missing_fields = [field for field in required_fields if field not in result]
        
        if missing_fields:
            print(f"✗ 结果 {i+1} 缺少字段: {missing_fields}")
            return False
    
    # 检查相关性
    relevant_count = 0
    for result in results:
        content = result['content'].lower()
        if any(keyword.lower() in content for keyword in expected_keywords):
            relevant_count += 1
    
    relevance_ratio = relevant_count / len(results)
    print(f"✓ 相关性比例: {relevance_ratio:.2%}")
    
    if relevance_ratio >= 0.5:  # 至少50%相关
        print("✓ 查询结果验证通过")
        return True
    else:
        print("✗ 查询结果相关性不足")
        return False

# 使用示例
expected_keywords = ["Python", "编程", "规范", "最佳实践"]
is_valid = await verify_query_results(results, expected_keywords)
```

### 第七步：性能测试

#### 7.1 响应时间测试

```python
# examples/performance_test.py
import time
import statistics

async def response_time_test(kb_id: int, llm_config: LLMConfig):
    """响应时间测试"""
    print("=== 响应时间测试 ===")
    
    db = next(get_db())
    kb_service = KnowledgeBaseService(db)
    
    test_queries = [
        "什么是RAG？",
        "如何使用Python？",
        "系统架构设计",
        "文档处理流程",
        "性能优化方法"
    ]
    
    response_times = []
    
    for query in test_queries:
        start_time = time.time()
        
        try:
            results = await kb_service.query_rag(
                knowledge_base_id=kb_id,
                query=query,
                llm_config=llm_config,
                top_k=5
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            response_times.append(response_time)
            
            print(f"查询: {query[:20]}... - {response_time:.2f}s ({len(results)}个结果)")
            
        except Exception as e:
            print(f"查询失败: {query[:20]}... - {e}")
    
    if response_times:
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        
        print(f"\n性能统计:")
        print(f"  平均响应时间: {avg_time:.2f}s")
        print(f"  最大响应时间: {max_time:.2f}s")
        print(f"  最小响应时间: {min_time:.2f}s")
        
        # 性能评估
        if avg_time < 2.0:
            print("✓ 性能优秀")
        elif avg_time < 5.0:
            print("✓ 性能良好")
        else:
            print("⚠ 性能需要优化")
    
    return response_times
```

#### 7.2 并发测试

```python
async def concurrency_test(kb_id: int, llm_config: LLMConfig, concurrent_users: int = 5):
    """并发测试"""
    print(f"=== 并发测试 ({concurrent_users}个并发用户) ===")
    
    import asyncio
    
    async def single_user_test(user_id: int):
        """单用户测试"""
        db = next(get_db())
        kb_service = KnowledgeBaseService(db)
        
        query = f"用户{user_id}的测试查询"
        start_time = time.time()
        
        try:
            results = await kb_service.query_rag(
                knowledge_base_id=kb_id,
                query=query,
                llm_config=llm_config,
                top_k=3
            )
            
            end_time = time.time()
            return {
                "user_id": user_id,
                "success": True,
                "response_time": end_time - start_time,
                "result_count": len(results)
            }
            
        except Exception as e:
            end_time = time.time()
            return {
                "user_id": user_id,
                "success": False,
                "response_time": end_time - start_time,
                "error": str(e)
            }
    
    # 并发执行
    start_time = time.time()
    tasks = [single_user_test(i) for i in range(concurrent_users)]
    results = await asyncio.gather(*tasks)
    total_time = time.time() - start_time
    
    # 统计结果
    successful_requests = [r for r in results if r["success"]]
    failed_requests = [r for r in results if not r["success"]]
    
    print(f"总耗时: {total_time:.2f}s")
    print(f"成功请求: {len(successful_requests)}/{concurrent_users}")
    print(f"失败请求: {len(failed_requests)}")
    
    if successful_requests:
        avg_response_time = statistics.mean([r["response_time"] for r in successful_requests])
        print(f"平均响应时间: {avg_response_time:.2f}s")
    
    return results
```

### 第八步：系统维护

#### 8.1 缓存管理

```python
# examples/cache_management.py
async def cache_management_example():
    """缓存管理示例"""
    print("=== 缓存管理 ===")
    
    from app.rag.retrieval.query_cache import QueryCache
    from app.rag.index_processor.index_cache import IndexCache
    
    # 查看缓存统计
    query_stats = await QueryCache.get_cache_stats()
    print(f"查询缓存统计:")
    print(f"  缓存条目数: {query_stats.get('count', 0)}")
    print(f"  命中率: {query_stats.get('hit_rate', 0):.2%}")
    
    # 清理过期缓存
    cleaned_count = await QueryCache.cleanup_expired()
    print(f"✓ 清理过期缓存: {cleaned_count} 条")
    
    # 清空所有缓存
    await QueryCache.clear_all_cache()
    print("✓ 清空所有查询缓存")
    
    await IndexCache.clear_all_cache()
    print("✓ 清空所有索引缓存")
```

#### 8.2 索引优化

```python
async def index_optimization_example(kb_id: int):
    """索引优化示例"""
    print("=== 索引优化 ===")
    
    db = next(get_db())
    kb_service = KnowledgeBaseService(db)
    
    try:
        # 优化向量索引
        optimization_result = await kb_service.optimize_vector_index(kb_id)
        print(f"✓ 向量索引优化完成")
        print(f"  优化前大小: {optimization_result.get('before_size', 'N/A')}")
        print(f"  优化后大小: {optimization_result.get('after_size', 'N/A')}")
        
        # 重建索引（如果需要）
        if optimization_result.get('needs_rebuild'):
            print("开始重建索引...")
            await kb_service.rebuild_index(kb_id)
            print("✓ 索引重建完成")
            
    except Exception as e:
        print(f"✗ 索引优化失败: {e}")
```

### 完整流程脚本

```python
# examples/complete_workflow.py
async def complete_workflow_example():
    """完整工作流程示例"""
    print("=== RAG知识库完整工作流程 ===")
    
    try:
        # 第一步：验证环境
        if not await verify_environment():
            return False
        
        # 第二步：创建知识库
        kb = await create_knowledge_base_example()
        if not kb:
            return False
        
        kb_id = kb.id
        
        # 第三步：上传文档
        file_paths = create_test_documents()
        documents = await upload_documents_example(kb_id, file_paths)
        if not documents:
            return False
        
        # 第四步：配置LLM
        llm_config = create_llm_config()
        if not await verify_llm_config(llm_config):
            return False
        
        # 第五步：执行训练
        training_result = await train_knowledge_base_example(kb_id, llm_config)
        if not training_result:
            return False
        
        # 监控训练进度
        await monitor_training_progress(kb_id)
        
        # 验证训练结果
        if not await verify_training_result(kb_id):
            return False
        
        # 第六步：执行查询
        await query_knowledge_base_example(kb_id, llm_config)
        await advanced_query_example(kb_id, llm_config)
        
        # 第七步：性能测试
        response_times = await response_time_test(kb_id, llm_config)
        concurrency_results = await concurrency_test(kb_id, llm_config)
        
        # 第八步：系统维护
        await cache_management_example()
        await index_optimization_example(kb_id)
        
        print("\n=== 完整工作流程执行成功 ===")
        return True
        
    except Exception as e:
        print(f"\n=== 工作流程执行失败: {e} ===")
        return False

if __name__ == "__main__":
    success = asyncio.run(complete_workflow_example())
    if success:
        print("✓ 所有测试通过，系统运行正常")
    else:
        print("✗ 测试失败，请检查系统配置")
```

## 使用建议

### 1. 开发环境使用

```bash
# 开发环境快速启动
export VECTOR_DB_TYPE=chroma
export RAG_CHUNK_SIZE=500
export RAG_LOG_LEVEL=DEBUG

python examples/complete_workflow.py
```

### 2. 生产环境使用

```bash
# 生产环境配置
export VECTOR_DB_TYPE=qdrant
export QDRANT_HOST=your-qdrant-host
export RAG_CHUNK_SIZE=1000
export RAG_ENABLE_RERANK=true
export RAG_LOG_LEVEL=INFO

python examples/complete_workflow.py
```

### 3. 性能调优

- **文档处理**: 根据文档类型调整chunk_size
- **向量化**: 使用合适的batch_size
- **检索**: 启用缓存和重排序
- **并发**: 根据硬件配置调整max_workers

### 4. 监控和维护

- 定期检查系统性能
- 清理过期缓存
- 优化向量索引
- 备份重要数据

---

*本使用流程文档提供了RAG功能的完整使用指南，包含详细的代码示例和验证方法。建议按照流程逐步执行，确保每个步骤都正确完成。*