# RAG知识库训练功能用户指南

## 概述

RAG（Retrieval-Augmented Generation）知识库训练功能是一个强大的文档处理和智能检索系统，支持多种文档格式的处理、向量化存储和智能检索。本指南将帮助您了解如何使用这些功能。

## 功能特性

### 支持的文档格式
- PDF文档
- Word文档（.docx）
- Excel文档（.xlsx）
- Markdown文档（.md）
- HTML文档（.html）
- 纯文本文档（.txt）

### 核心功能
- 智能文档解析和内容提取
- 多种文本分块策略
- 向量化存储和索引
- 多种检索方式（语义搜索、关键词搜索、混合搜索）
- 检索结果重排序
- 缓存优化
- 异步处理

## 快速开始

### 1. 创建知识库

首先，您需要创建一个知识库：

```python
from app.services.knowledge_base import KnowledgeBaseService
from app.models.knowledge_base import KnowledgeBase

# 创建知识库服务实例
kb_service = KnowledgeBaseService(db_session)

# 创建知识库
knowledge_base = await kb_service.create_knowledge_base(
    name="我的知识库",
    description="用于存储技术文档的知识库",
    user_id=user_id
)
```

### 2. 上传文档

将文档上传到知识库：

```python
# 上传文档
document = await kb_service.upload_document(
    knowledge_base_id=knowledge_base.id,
    file_path="/path/to/document.pdf",
    title="技术文档",
    user_id=user_id
)
```

### 3. 训练知识库

对知识库进行RAG训练：

```python
# 配置LLM
from app.models.llm_config import LLMConfig

llm_config = LLMConfig(
    embeddings={
        "provider": "openai",
        "model": "text-embedding-ada-002",
        "api_key": "your-api-key"
    }
)

# 开始训练
training_result = await kb_service.train_rag(
    knowledge_base_id=knowledge_base.id,
    llm_config=llm_config,
    user_id=user_id
)
```

### 4. 查询知识库

训练完成后，您可以查询知识库：

```python
# 查询知识库
results = await kb_service.query_rag(
    knowledge_base_id=knowledge_base.id,
    query="如何配置系统？",
    llm_config=llm_config,
    method="semantic_search",
    top_k=5,
    user_id=user_id
)

# 处理结果
for result in results:
    print(f"内容: {result['content']}")
    print(f"相关度: {result['score']}")
    print(f"来源: {result['document']['title']}")
```

## 详细使用说明

### 文档处理配置

#### 文本分块配置

系统支持多种文本分块策略：

```python
# 递归字符分块（推荐）
chunk_config = {
    "strategy": "recursive_character",
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "separators": ["\n\n", "\n", " ", ""]
}

# 固定长度分块
chunk_config = {
    "strategy": "fixed",
    "chunk_size": 500,
    "chunk_overlap": 50
}
```

#### 向量化配置

支持多种向量化模型：

```python
# OpenAI Embedding
embedding_config = {
    "provider": "openai",
    "model": "text-embedding-ada-002",
    "api_key": "your-api-key",
    "batch_size": 100
}

# 本地模型
embedding_config = {
    "provider": "huggingface",
    "model": "sentence-transformers/all-MiniLM-L6-v2",
    "batch_size": 50
}
```

### 向量存储配置

#### Chroma配置

```python
vector_config = {
    "type": "chroma",
    "persist_directory": "./chroma_db",
    "collection_name": "knowledge_base"
}
```

#### Qdrant配置

```python
vector_config = {
    "type": "qdrant",
    "host": "localhost",
    "port": 6333,
    "collection_name": "knowledge_base",
    "vector_size": 1536
}
```

### 检索配置

#### 语义搜索

```python
search_config = {
    "method": "semantic_search",
    "top_k": 10,
    "score_threshold": 0.7
}
```

#### 关键词搜索

```python
search_config = {
    "method": "keyword_search",
    "top_k": 10,
    "use_stemming": True
}
```

#### 混合搜索

```python
search_config = {
    "method": "hybrid_search",
    "top_k": 10,
    "semantic_weight": 0.7,
    "keyword_weight": 0.3
}
```

### 重排序配置

```python
rerank_config = {
    "use_rerank": True,
    "rerank_mode": "weighted_score",
    "rerank_top_k": 20,
    "final_top_k": 5
}
```

## 高级功能

### 批量处理

对于大量文档的处理，建议使用批量处理：

```python
# 批量上传文档
documents = await kb_service.batch_upload_documents(
    knowledge_base_id=knowledge_base.id,
    file_paths=[
        "/path/to/doc1.pdf",
        "/path/to/doc2.docx",
        "/path/to/doc3.md"
    ],
    user_id=user_id
)

# 批量训练
await kb_service.batch_train_documents(
    knowledge_base_id=knowledge_base.id,
    document_ids=[doc.id for doc in documents],
    llm_config=llm_config,
    user_id=user_id
)
```

### 缓存优化

系统自动启用缓存优化，您也可以手动控制：

```python
# 查询时禁用缓存
results = await kb_service.query_rag(
    knowledge_base_id=knowledge_base.id,
    query="查询内容",
    llm_config=llm_config,
    use_cache=False,  # 禁用缓存
    user_id=user_id
)

# 清除缓存
from app.rag.retrieval.query_cache import QueryCache
await QueryCache.clear_cache(knowledge_base_id=knowledge_base.id)
```

### 异步处理

对于大型文档或大量文档，建议使用异步处理：

```python
from app.utils.tasks import train_rag_knowledge_base

# 提交异步训练任务
task = train_rag_knowledge_base.schedule(
    args=(knowledge_base.id, llm_config.dict(), user_id),
    delay=0
)

# 检查任务状态
task_status = await kb_service.get_training_status(knowledge_base.id)
print(f"训练状态: {task_status}")
```

## 监控和管理

### 训练状态监控

```python
# 获取训练状态
status = await kb_service.get_training_status(knowledge_base.id)
print(f"状态: {status['status']}")
print(f"进度: {status['progress']}%")
print(f"处理文档数: {status['processed_documents']}")
print(f"总文档数: {status['total_documents']}")
```

### 性能监控

```python
# 获取性能统计
stats = await kb_service.get_performance_stats(knowledge_base.id)
print(f"平均查询时间: {stats['avg_query_time']}ms")
print(f"缓存命中率: {stats['cache_hit_rate']}%")
print(f"索引大小: {stats['index_size']}MB")
```

### 日志查看

```python
# 获取训练日志
logs = await kb_service.get_training_logs(
    knowledge_base.id,
    limit=100,
    level="INFO"
)

for log in logs:
    print(f"[{log['timestamp']}] {log['level']}: {log['message']}")
```

## 最佳实践

### 1. 文档准备

- **文档质量**: 确保文档内容清晰、结构化
- **文档大小**: 单个文档建议不超过50MB
- **文档格式**: 优先使用结构化格式（Markdown、HTML）

### 2. 分块策略

- **技术文档**: 使用递归字符分块，chunk_size=1000-1500
- **长篇文章**: 使用递归字符分块，chunk_size=2000-3000
- **代码文档**: 使用固定长度分块，chunk_size=500-800

### 3. 向量化选择

- **高精度需求**: 使用OpenAI text-embedding-ada-002
- **成本敏感**: 使用开源模型如all-MiniLM-L6-v2
- **多语言支持**: 使用multilingual-e5-large

### 4. 检索优化

- **精确匹配**: 优先使用关键词搜索
- **语义理解**: 优先使用语义搜索
- **综合效果**: 使用混合搜索

### 5. 性能优化

- **启用缓存**: 对于重复查询场景
- **批量处理**: 对于大量文档处理
- **异步处理**: 对于耗时操作

## 故障排除

### 常见问题

#### 1. 文档上传失败

**问题**: 文档上传时出现错误

**解决方案**:
```python
try:
    document = await kb_service.upload_document(...)
except DocumentProcessingError as e:
    print(f"文档处理错误: {e}")
    # 检查文档格式和大小
    # 确保文档没有损坏
except PermissionError as e:
    print(f"权限错误: {e}")
    # 检查用户权限
```

#### 2. 训练失败

**问题**: 知识库训练过程中失败

**解决方案**:
```python
try:
    await kb_service.train_rag(...)
except EmbeddingError as e:
    print(f"向量化错误: {e}")
    # 检查LLM配置
    # 检查API密钥
except VectorStoreError as e:
    print(f"向量存储错误: {e}")
    # 检查向量数据库连接
    # 检查存储空间
```

#### 3. 查询无结果

**问题**: 查询知识库时返回空结果

**解决方案**:
```python
# 降低相似度阈值
results = await kb_service.query_rag(
    ...,
    score_threshold=0.5  # 降低阈值
)

# 增加返回结果数量
results = await kb_service.query_rag(
    ...,
    top_k=20  # 增加数量
)

# 尝试不同的检索方法
results = await kb_service.query_rag(
    ...,
    method="hybrid_search"  # 使用混合搜索
)
```

#### 4. 性能问题

**问题**: 查询响应时间过长

**解决方案**:
```python
# 启用缓存
results = await kb_service.query_rag(
    ...,
    use_cache=True
)

# 减少返回结果数量
results = await kb_service.query_rag(
    ...,
    top_k=5  # 减少数量
)

# 优化向量数据库配置
# 检查系统资源使用情况
```

### 错误代码说明

| 错误代码 | 说明 | 解决方案 |
|---------|------|----------|
| RAG_001 | 文档格式不支持 | 检查文档格式，使用支持的格式 |
| RAG_002 | 向量化失败 | 检查LLM配置和API密钥 |
| RAG_003 | 向量存储连接失败 | 检查向量数据库连接配置 |
| RAG_004 | 索引构建失败 | 检查存储空间和权限 |
| RAG_005 | 查询超时 | 优化查询参数或增加超时时间 |

### 日志分析

#### 启用详细日志

```python
import logging

# 设置日志级别
logging.getLogger("app.rag").setLevel(logging.DEBUG)

# 查看详细日志
logs = await kb_service.get_training_logs(
    knowledge_base.id,
    level="DEBUG"
)
```

#### 关键日志信息

- **文档处理**: 查看文档解析和分块日志
- **向量化**: 查看向量生成和存储日志
- **索引构建**: 查看索引创建和更新日志
- **查询执行**: 查看检索和重排序日志

## 配置参考

### 环境变量配置

```bash
# 向量数据库配置
VECTOR_DB_TYPE=chroma
CHROMA_PERSIST_DIRECTORY=./chroma_db
QDRANT_HOST=localhost
QDRANT_PORT=6333

# 缓存配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# 性能配置
RAG_BATCH_SIZE=100
RAG_MAX_WORKERS=4
RAG_TIMEOUT=300
```

### 配置文件示例

```yaml
# config/rag.yaml
rag:
  document_processing:
    max_file_size: 52428800  # 50MB
    supported_formats:
      - pdf
      - docx
      - xlsx
      - md
      - html
      - txt
  
  text_splitting:
    default_strategy: recursive_character
    chunk_size: 1000
    chunk_overlap: 200
  
  embedding:
    batch_size: 100
    cache_ttl: 604800  # 7 days
  
  vector_store:
    type: chroma
    config:
      persist_directory: ./chroma_db
  
  retrieval:
    default_top_k: 10
    score_threshold: 0.7
    enable_rerank: true
```

## 更新和维护

### 版本升级

在升级系统时，请注意：

1. **备份数据**: 升级前备份向量数据库和配置文件
2. **迁移脚本**: 运行必要的数据库迁移脚本
3. **配置更新**: 检查和更新配置文件
4. **功能测试**: 升级后进行功能测试

### 定期维护

建议定期执行以下维护任务：

```python
# 清理过期缓存
await QueryCache.cleanup_expired()

# 优化向量索引
await kb_service.optimize_vector_index(knowledge_base.id)

# 清理训练日志
await kb_service.cleanup_training_logs(days=30)
```

## 支持和帮助

如果您在使用过程中遇到问题，可以：

1. 查看详细的错误日志
2. 参考本指南的故障排除部分
3. 检查系统配置和环境
4. 联系技术支持团队

---

*本指南将持续更新，请关注最新版本。*