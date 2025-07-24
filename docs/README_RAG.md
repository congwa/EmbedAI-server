# RAG知识库训练功能

## 概述

RAG（Retrieval-Augmented Generation）知识库训练功能是一个完整的文档处理和智能检索系统，支持多种文档格式的处理、向量化存储和智能检索。

## 功能特性

### 🔧 核心功能
- **多格式文档支持**: PDF、Word、Excel、Markdown、HTML、TXT
- **智能文档解析**: 自动提取文档内容和结构
- **灵活文本分块**: 支持多种分块策略（递归字符、固定长度、语义分块）
- **向量化存储**: 支持多种向量数据库（Chroma、Qdrant）
- **多种检索方式**: 语义搜索、关键词搜索、混合搜索
- **结果重排序**: 多种重排序算法优化检索结果
- **缓存优化**: 查询结果和向量缓存，提升性能
- **异步处理**: 支持大文档和批量处理

### 🚀 性能特性
- **批量处理**: 高效处理大量文档
- **并发支持**: 多用户并发访问
- **缓存机制**: Redis缓存提升响应速度
- **索引优化**: 向量索引自动优化
- **内存管理**: 智能内存使用和垃圾回收

### 🛡️ 安全特性
- **权限控制**: 基于用户的访问控制
- **文件验证**: 文件类型和大小验证
- **错误处理**: 完善的异常处理机制
- **审计日志**: 详细的操作日志记录

## 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置必要的参数
```

### 2. 系统验证

```bash
# 快速健康检查
python scripts/quick_validation.py

# 完整系统验证
python scripts/validate_rag_system.py
```

### 3. 基础使用

```python
from app.services.knowledge_base import KnowledgeBaseService
from app.models.llm_config import LLMConfig

# 创建知识库
kb_service = KnowledgeBaseService(db_session)
kb = await kb_service.create_knowledge_base(
    name="我的知识库",
    description="技术文档知识库",
    user_id=user_id
)

# 上传文档
document = await kb_service.upload_document(
    knowledge_base_id=kb.id,
    file_path="document.pdf",
    title="技术文档",
    user_id=user_id
)

# 配置LLM
llm_config = LLMConfig(
    embeddings={
        "provider": "openai",
        "model": "text-embedding-ada-002",
        "api_key": "your-api-key"
    }
)

# 训练知识库
await kb_service.train_rag(
    knowledge_base_id=kb.id,
    llm_config=llm_config,
    user_id=user_id
)

# 查询知识库
results = await kb_service.query_rag(
    knowledge_base_id=kb.id,
    query="如何使用RAG功能？",
    llm_config=llm_config,
    top_k=5,
    user_id=user_id
)
```

## 文档指南

### 📖 用户指南
- [**完整用户指南**](user_guide/rag_user_guide.md) - 详细的功能介绍和使用方法
- [**配置指南**](user_guide/rag_configuration_guide.md) - 系统配置和优化
- [**故障排除指南**](user_guide/rag_troubleshooting_guide.md) - 常见问题和解决方案
- [**使用流程**](user_guide/rag_usage_workflow.md) - 完整的使用流程和验证方法

### 🔧 技术文档
- [**API文档**](api/rag_knowledge_base.md) - API接口详细说明
- [**架构设计**](../specs/rag-knowledge-base-training/design.md) - 系统架构和设计
- [**需求文档**](../specs/rag-knowledge-base-training/requirements.md) - 功能需求和验收标准

## 系统架构

```
RAG知识库训练系统
├── 文档处理层
│   ├── 文档提取器 (PDF, Word, Excel, etc.)
│   ├── 文本清理器
│   └── 文本分块器
├── 向量化层
│   ├── 向量化引擎
│   ├── 缓存向量化
│   └── 批量处理
├── 存储层
│   ├── 向量数据库 (Chroma/Qdrant)
│   ├── 关系数据库 (PostgreSQL/SQLite)
│   └── 缓存系统 (Redis)
├── 检索层
│   ├── 语义搜索
│   ├── 关键词搜索
│   ├── 混合搜索
│   └── 结果重排序
└── 服务层
    ├── 知识库服务
    ├── 训练管理器
    ├── 检索服务
    └── 缓存管理
```

## 配置示例

### 开发环境配置

```bash
# .env.development
VECTOR_DB_TYPE=chroma
CHROMA_PERSIST_DIRECTORY=./data/dev/chroma_db
RAG_CHUNK_SIZE=500
RAG_EMBEDDING_BATCH_SIZE=50
RAG_LOG_LEVEL=DEBUG
```

### 生产环境配置

```bash
# .env.production
VECTOR_DB_TYPE=qdrant
QDRANT_HOST=your-qdrant-host
QDRANT_PORT=6333
RAG_CHUNK_SIZE=1000
RAG_EMBEDDING_BATCH_SIZE=100
RAG_ENABLE_RERANK=true
RAG_LOG_LEVEL=INFO
```

## 性能优化

### 文档处理优化
- 根据文档类型选择合适的分块大小
- 使用批量处理提高效率
- 启用异步处理处理大文档

### 向量化优化
- 选择合适的向量化模型
- 使用批量向量化
- 启用向量缓存

### 检索优化
- 使用混合搜索提高准确性
- 启用结果重排序
- 配置合适的缓存策略

### 系统优化
- 监控内存使用
- 定期清理缓存
- 优化向量索引

## 监控和维护

### 健康检查

```bash
# 快速检查
python scripts/quick_validation.py

# 详细检查
python scripts/validate_rag_system.py
```

### 性能监控

```python
# 获取性能统计
stats = await kb_service.get_performance_stats(kb_id)
print(f"平均查询时间: {stats['avg_query_time']}ms")
print(f"缓存命中率: {stats['cache_hit_rate']}%")
```

### 定期维护

```bash
# 清理过期缓存
python -c "
import asyncio
from app.rag.retrieval.query_cache import QueryCache
asyncio.run(QueryCache.cleanup_expired())
"

# 优化向量索引
python -c "
import asyncio
from app.services.knowledge_base import KnowledgeBaseService
# 优化指定知识库的索引
"
```

## 故障排除

### 常见问题

1. **文档上传失败**
   - 检查文档格式和大小
   - 验证文件权限
   - 查看错误日志

2. **训练失败**
   - 检查LLM配置
   - 验证向量数据库连接
   - 检查系统资源

3. **查询无结果**
   - 降低相似度阈值
   - 尝试不同检索方法
   - 检查索引状态

4. **性能问题**
   - 启用缓存
   - 优化查询参数
   - 检查系统资源

### 获取帮助

- 查看详细的[故障排除指南](user_guide/rag_troubleshooting_guide.md)
- 检查系统日志文件
- 运行系统诊断脚本

## 版本信息

- **当前版本**: 1.0.0
- **Python版本**: 3.8+
- **主要依赖**: FastAPI, SQLAlchemy, Redis, ChromaDB/Qdrant

## 更新日志

### v1.0.0 (2024-01-XX)
- ✨ 初始版本发布
- 🔧 支持多种文档格式处理
- 🚀 实现向量化存储和检索
- 🛡️ 完善的权限控制和错误处理
- 📖 完整的文档和使用指南

## 贡献指南

欢迎贡献代码和改进建议！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](../LICENSE) 文件。

---

*如有问题或建议，请创建 Issue 或联系开发团队。*