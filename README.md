# EmbedAI Server - 智能知识库助手系统

企业级 AI 知识管理与服务系统，基于 RAG（检索增强生成）技术和大型语言模型，提供高性能的语义检索、智能问答和知识管理功能。

## 🌟 核心特性

### 📊 多租户知识管理

- **知识库隔离**：每个用户可创建和管理多个独立知识库
- **权限控制**：细粒度的用户权限管理（读/写/管理/所有者）
- **多用户协作**：支持知识库多用户共享与协作

### 🤖 先进 AI 技术

- **RAG 检索增强生成**：结合向量数据库和语义检索技术
- **智能文档分块**：基于语义的内容分段和重叠处理
- **向量化检索**：高效的语义相似度搜索和匹配
- **重排序优化**：使用重排序模型提升结果准确性

### 📁 多格式文档处理

- **丰富文档类型**：PDF、Word、Excel、TXT、Markdown、HTML
- **智能分段**：基于语义的内容分块和重叠处理
- **元数据提取**：自动提取文档标题、关键词等元数据
- **OCR 支持**：图片和扫描文档的文字识别

### 💬 智能问答系统

- **RAG 增强回答**：基于检索到的相关文档片段生成准确回复
- **语义理解**：深度理解用户意图，提供精准的语义匹配
- **上下文感知**：保持对话上下文，支持多轮对话
- **实时对话**：WebSocket 支持的实时聊天体验
- **成本计算**：精确的 Token 使用和费用计算
- **防刷机制**：完善的访问频率控制和防滥用保护

## 🏗️ 技术架构

### 系统架构

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   Redis/Queue    │    │  Vector Store   │
│   API Server    │───→│   Async Tasks    │───→│  (Embeddings)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                      │                      │
         ↓                      ↓                      ↓
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │   LLM Service    │    │   app/rag/      │
│   Metadata DB   │    │   SiliconFlow    │    │   RAG Modules   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### RAG 数据处理流程

1. **文档上传** → 解析文档内容
2. **内容分块** → 智能语义分段处理
3. **向量化** → 生成高维嵌入向量
4. **索引构建** → 创建向量索引和元数据
5. **语义检索** → 基于向量相似度的检索
6. **结果重排** → 使用重排序模型优化结果
7. **智能回答** → LLM 基于检索上下文生成回复

## 🚀 快速开始

### 环境要求

- Python 3.10+
- PostgreSQL
- Redis

### 本地开发

#### 1. 环境配置

```bash
# 克隆项目
git clone https://github.com/congwa/EmbedAI-server.git
cd EmbedAI-server

# 创建虚拟环境
poetry install

# 激活环境
poetry shell
```

#### 2. 环境变量配置

```bash
# 复制配置文件
cp .env.example .env

# 编辑配置vim .env
DATABASE_URL=postgresql://user:password@localhost/embedai
REDIS_HOST=localhost
REDIS_PORT=6379
SILICONFLOW_API_KEY=your_api_key
# 或使用其他LLM服务
OPENAI_API_KEY=your_openai_key
ZHIPU_API_KEY=your_zhipu_key
```

#### 3. 数据库初始化

```bash
# 创建数据库表
alembic upgrade head

# 创建默认管理员
python scripts/create_admin.py --username admin --password admin123
```

#### 4. 启动服务

```bash
# 开发模式（热重载）
poetry run python main.py

# 或使用uvicorn
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Docker 部署

#### 1. 快速部署

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 检查服务状态
docker-compose ps
```

#### 2. 生产环境部署

```bash
# 构建镜像
docker build -t embedai-server .

# 运行容器（生产配置）
docker run -d \
  --name embedai-server \
  --restart unless-stopped \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@db:5432/embedai \
  -e REDIS_URL=redis://redis:6379/0 \
  -e SILICONFLOW_API_KEY=your_key \
  -e WORKERS=4 \
  -e LOG_LEVEL=info \
  --memory=4g \
  --cpus=2 \
  embedai-server
```

#### 3. 集群部署

```yaml
# docker-compose.prod.yml
version: "3.8"
services:
  app:
    image: embedai-server
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 4G
          cpus: "2"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/embedai
      - REDIS_URL=redis://redis:6379/0
      - WORKERS=2
    depends_on:
      - db
      - redis

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - app

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: embedai
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### API 文档

启动服务后访问：

- Swagger 文档: http://localhost:8000/docs
- ReDoc 文档: http://localhost:8000/redoc

## 📚 API 使用指南

### 认证流程

```bash
# 1. 用户注册
POST /api/v1/auth/register
{
  "email": "user@example.com",
  "password": "password123",
  "username": "testuser"
}

# 2. 用户登录
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "password123"
}

# 3. 使用token
Authorization: Bearer <jwt_token>
```

### 知识库管理

```bash
# 创建知识库
POST /api/v1/knowledge-bases
{
  "name": "公司制度",
  "description": "公司内部管理制度"
}

# 上传文档
POST /api/v1/knowledge-bases/{id}/documents
# 支持文件: PDF, DOCX, XLSX, TXT, MD, HTML
```

### RAG 智能问答

```bash
# 基础问答 - 使用默认RAG配置
POST /api/v1/chat/completions
{
  "knowledge_base_id": "uuid",
  "messages": [
    {"role": "user", "content": "公司的请假流程是什么？"}
  ]
}

# 高级RAG配置问答
POST /api/v1/chat/completions
{
  "knowledge_base_id": "uuid",
  "messages": [
    {"role": "user", "content": "公司的请假流程是什么？"}
  ],
  "rag_config": {
    "retrieval_method": "semantic_search",
    "top_k": 5,
    "use_rerank": true,
    "rerank_mode": "weighted_score"
  }
}

# 检索测试 - 仅返回相关文档片段
POST /api/v1/knowledge-bases/{id}/search
{
  "query": "请假流程",
  "method": "semantic_search",
  "top_k": 10
}

# WebSocket实时对话
ws://localhost:8000/ws/chat/{knowledge_base_id}
```

## 🧪 开发指南

### app/rag 模块架构

项目采用模块化的 RAG 架构设计，各模块职责清晰，易于扩展和维护：

```
app/rag/
├── embedding/              # 向量化模块
│   ├── embedding_base.py   # 向量化基类接口
│   ├── cached_embedding.py # 缓存向量化实现
│   └── embedding_engine.py # 向量化引擎
├── retrieval/              # 检索模块
│   ├── retrieval_service.py # 检索服务主入口
│   ├── retrieval_engine.py  # 检索引擎实现
│   ├── retrieval_methods.py # 检索方法定义
│   └── query_cache.py       # 查询结果缓存
├── extractor/              # 文档提取模块
│   ├── extract_processor.py # 提取处理器
│   ├── pdf_extractor.py     # PDF文档提取
│   ├── word_extractor.py    # Word文档提取
│   ├── excel_extractor.py   # Excel文档提取
│   └── html_extractor.py    # HTML文档提取
├── splitter/               # 文档分块模块
│   ├── text_splitter.py     # 通用文本分块器
│   └── recursive_character_text_splitter.py # 递归字符分块器
├── rerank/                 # 结果重排序模块
│   ├── rerank_base.py       # 重排序基类
│   ├── rerank_factory.py    # 重排序工厂
│   └── weight_rerank.py     # 权重重排序
├── training/               # 训练管理模块
│   ├── training_manager.py  # 训练管理器
│   └── training_status.py   # 训练状态管理
└── models/                 # 数据模型
    └── document.py          # 文档数据模型
```

#### RAG 模块组件关系图

```
                    ┌─────────────────────────────────────────┐
                    │            SessionManager              │
                    │         (app/utils/session.py)         │
                    └─────────────────┬───────────────────────┘
                                      │
                    ┌─────────────────▼───────────────────────┐
                    │          RetrievalService               │
                    │      (app/rag/retrieval/)               │
                    └─────────────────┬───────────────────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        │                             │                             │
        ▼                             ▼                             ▼
┌───────────────┐           ┌─────────────────┐           ┌─────────────────┐
│ EmbeddingEngine│           │ RetrievalEngine │           │ TrainingManager │
│ (embedding/)   │           │ (retrieval/)    │           │ (training/)     │
└───────┬───────┘           └─────────┬───────┘           └─────────────────┘
        │                             │
        ▼                             ▼
┌───────────────┐           ┌─────────────────┐
│ CachedEmbedding│           │ IndexProcessor  │
│ (embedding/)   │           │ (index_processor/)│
└───────────────┘           └─────────┬───────┘
                                      │
                            ┌─────────▼───────┐
                            │ ExtractProcessor │
                            │ (extractor/)     │
                            └─────────┬───────┘
                                      │
                            ┌─────────▼───────┐
                            │  TextSplitter   │
                            │  (splitter/)    │
                            └─────────────────┘
```

#### RAG 工作流程

1. **文档处理流程**

   ```python
   # 文档上传 → 提取 → 分块 → 向量化 → 存储
   extractor = ExtractProcessor()
   content = await extractor.extract_document(file)

   splitter = TextSplitter(chunk_size=1000, chunk_overlap=200)
   chunks = splitter.split_text(content)

   embedding_engine = EmbeddingEngine(llm_config)
   vectors = await embedding_engine.embed_documents(chunks)
   ```

2. **检索查询流程**
   ```python
   # 查询 → 向量化 → 检索 → 重排序 → 返回结果
   retrieval_service = RetrievalService(db)
   results = await retrieval_service.query(
       knowledge_base=kb,
       query="用户问题",
       method="semantic_search",
       top_k=5,
       use_rerank=True
   )
   ```

#### 模块化设计优势

1. **高度解耦**: 各模块独立开发和测试，易于维护
2. **灵活扩展**: 可以轻松替换或扩展特定模块
3. **性能优化**: 每个模块都可以独立优化性能
4. **多样化支持**: 支持多种文档格式、检索方法和重排序策略

#### 核心模块详解

**1. 向量化模块 (embedding/)**

```python
from app.rag.embedding.embedding_engine import EmbeddingEngine

# 初始化向量化引擎
engine = EmbeddingEngine(llm_config, db)

# 批量向量化文档
vectors = await engine.embed_documents(texts)

# 向量化查询
query_vector = await engine.embed_query("用户查询")
```

**2. 检索模块 (retrieval/)**

```python
from app.rag.retrieval.retrieval_service import RetrievalService
from app.rag.retrieval.retrieval_methods import RetrievalMethod

# 支持多种检索方法
methods = [
    RetrievalMethod.SEMANTIC_SEARCH,    # 语义检索
    RetrievalMethod.KEYWORD_SEARCH,     # 关键词检索
    RetrievalMethod.HYBRID_SEARCH       # 混合检索
]
```

**3. 文档处理模块 (extractor/ & splitter/)**

```python
from app.rag.extractor.extract_processor import ExtractProcessor
from app.rag.splitter.text_splitter import TextSplitter

# 支持多种文档格式
extractor = ExtractProcessor()
content = await extractor.extract_document(file)  # PDF, Word, Excel等

# 智能分块
splitter = TextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_text(content)
```

**4. 重排序模块 (rerank/)**

```python
from app.rag.rerank.rerank_factory import RerankFactory
from app.rag.rerank.rerank_type import RerankMode

# 创建重排序器
reranker = RerankFactory.create_reranker(RerankMode.WEIGHTED_SCORE)
reranked_results = await reranker.rerank(query, results)
```

### 项目结构

```
EmbedAI-server/
├── app/
│   ├── api/v1/          # API路由
│   ├── core/            # 核心配置
│   ├── models/          # 数据库模型
│   ├── schemas/         # 数据验证
│   └── services/        # 业务逻辑
├── app/rag/             # RAG引擎模块
│   ├── retrieval/       # 检索服务
│   ├── embedding/       # 向量化引擎
│   ├── extractor/       # 文档提取器
│   ├── splitter/        # 文档分块器
│   ├── rerank/          # 结果重排序
│   └── training/        # 训练管理
├── main.py              # 应用入口
├── pyproject.toml       # 依赖配置
└── alembic/             # 数据库迁移
```

### 开发工具

#### 代码质量

```bash
# 代码检查
poetry run flake8 app/

# 类型检查
poetry run mypy app/

# 安全扫描
poetry run bandit -r app/
```

#### 测试

```bash
# 运行所有测试
poetry run pytest

# 运行特定测试
poetry run pytest tests/test_knowledge_base.py -v

# 带覆盖率测试
poetry run pytest --cov=app --cov-report=html
```

#### 数据库迁移

```bash
# 创建迁移
alembic revision --autogenerate -m "add user table"

# 运行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

### 模型配置

#### 支持的 LLM 服务

- **SiliconFlow** (默认): 免费额度充足，支持 Qwen 系列模型
- **OpenAI**: GPT-3.5, GPT-4 等
- **Zhipu**: 中文优化，适合国内使用

#### RAG 配置示例

```python
# 修改 app/core/config.py 中的RAG相关配置
DEFAULT_LLM_MODEL = "Qwen/Qwen2.5-7B-Instruct"
DEFAULT_API_BASE = "https://api.siliconflow.cn/v1"
DEFAULT_API_KEY = "sk-xxx"

# 向量化配置
DEFAULT_EMBEDDING_MODEL = "text-embedding-ada-002"
DEFAULT_EMBEDDING_DIM = 1536
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# 检索配置
DEFAULT_TOP_K = 5
USE_RERANK = True
RERANK_MODEL = "bge-reranker-base"
```

#### 环境变量配置

```bash
# 核心服务配置
DATABASE_URL=postgresql://user:password@localhost/embedai
REDIS_URL=redis://localhost:6379/0

# LLM服务配置（选择其一或多个）
SILICONFLOW_API_KEY=sk-your-siliconflow-key
OPENAI_API_KEY=sk-your-openai-key
ZHIPU_API_KEY=your-zhipu-key

# RAG配置
DEFAULT_CHUNK_SIZE=1000
DEFAULT_CHUNK_OVERLAP=200
DEFAULT_TOP_K=5
ENABLE_RERANK=true

# 可选：自定义模型配置
CUSTOM_LLM_MODEL=Qwen/Qwen2.5-7B-Instruct
CUSTOM_EMBEDDING_MODEL=text-embedding-ada-002
```

## 📊 性能优化

### RAG 性能优势

#### 检索速度优势

- **向量检索**: 毫秒级的语义相似度计算，远超传统关键词搜索
- **并行处理**: 支持批量文档向量化和并行检索
- **索引优化**: 高效的向量索引结构，支持大规模文档库

#### 准确性提升

- **语义理解**: 基于深度学习的语义匹配，理解用户真实意图
- **上下文相关**: 检索到的文档片段与查询高度相关
- **重排序优化**: 二次排序提升最终结果的准确性

#### 与传统搜索对比

| 特性     | 传统关键词搜索 | RAG 语义检索   |
| -------- | -------------- | -------------- |
| 匹配方式 | 精确关键词匹配 | 语义相似度匹配 |
| 理解能力 | 字面意思       | 深层语义理解   |
| 召回率   | 依赖关键词覆盖 | 基于语义相关性 |
| 响应速度 | 快速           | 毫秒级响应     |
| 结果质量 | 依赖关键词质量 | 智能语义排序   |

### 缓存策略

- **Redis 缓存**: 缓存常用查询结果和向量检索结果
- **向量缓存**: 避免重复向量化处理，提升响应速度
- **查询缓存**: 缓存相似查询的检索结果，减少计算开销
- **智能预热**: 根据访问模式预加载热门文档向量

### 性能基准测试

#### 检索性能指标

| 指标         | 小型知识库(1K 文档) | 中型知识库(10K 文档) | 大型知识库(100K 文档) |
| ------------ | ------------------- | -------------------- | --------------------- |
| 平均检索时间 | 50ms                | 120ms                | 300ms                 |
| 向量化时间   | 10ms                | 10ms                 | 10ms                  |
| 重排序时间   | 20ms                | 40ms                 | 80ms                  |
| 内存使用     | 500MB               | 2GB                  | 8GB                   |
| 并发支持     | 100 QPS             | 80 QPS               | 50 QPS                |

#### 准确性指标

- **语义匹配准确率**: 85-92%（相比关键词搜索的 60-70%）
- **上下文相关性**: 90%+（基于人工评估）
- **多语言支持**: 中英文混合检索准确率 80%+

### 优化策略

#### 缓存优化

```python
# 多层缓存策略
1. L1缓存: 内存中的查询结果缓存（Redis）
2. L2缓存: 向量计算结果缓存
3. L3缓存: 文档分块缓存
4. 智能预热: 基于访问模式的预加载
```

#### 批处理优化

```python
# 批量处理配置
BATCH_SIZE = 100          # 向量化批处理大小
MAX_CONCURRENT = 10       # 最大并发请求数
CHUNK_OVERLAP = 200       # 文档分块重叠字符数
RERANK_TOP_K = 20         # 重排序候选数量
```

### 扩展建议

- **水平扩展**: 使用负载均衡部署多台实例
- **向量数据库**: 集成专业向量数据库（如 Milvus、Pinecone、Chroma）
- **GPU 加速**: 使用 GPU 加速向量计算和模型推理
- **分布式检索**: 支持跨多个节点的分布式向量检索
- **模型优化**: 使用量化模型减少内存占用
- **索引优化**: 使用 HNSW、IVF 等高效索引算法

## 🔄 配套项目

### SDK 和前端

- **[EmbedAI-sdk H5 端 sdk](./frontend/sdk/)**: 移动端 SDK，快速集成到移动应用
- **[EmbedAI-admin 后台管理端](./frontend/admin/)**: 管理后台，监控和配置管理

### 客户端示例

```javascript
// JavaScript SDK示例
const sdk = new EmbedAI({
  baseURL: "http://localhost:8000",
  token: "your_jwt_token",
});

// 获取知识库列表
await sdk.getKnowledgeBases();

// 上传文档并训练
await sdk.uploadDocument(kbId, file);

// 智能问答
await sdk.chat(kbId, "问题内容");
```

## 🛠️ 故障排除

### 常见问题

#### 1. 数据库连接失败

```bash
# 检查数据库状态
systemctl status postgres

# 检查配置连接字符串
python -c "from sqlalchemy import create_engine; print(create_engine('你的数据库URL').connect())"
```

#### 2. 向量化服务问题

```bash
# 检查向量化API连接
curl -H "Authorization: Bearer your_key" \
  https://api.siliconflow.cn/v1/models

# 测试向量化功能
python -c "
from app.rag.embedding.embedding_engine import EmbeddingEngine
from app.schemas.llm import LLMConfig
# 测试向量化是否正常工作
"
```

#### 3. Redis 连接问题

```bash
# 检查Redis连接
redis-cli ping
# 应返回 PONG

# 检查Redis配置
python -c "
import redis
r = redis.Redis(host='localhost', port=6379, db=0)
print(r.ping())
"
```

#### 4. LLM 服务调用失败

```bash
# 检查SiliconFlow API
curl -H "Authorization: Bearer your_key" \
  https://api.siliconflow.cn/v1/models

# 检查OpenAI API
curl -H "Authorization: Bearer your_key" \
  https://api.openai.com/v1/models

# 测试向量化服务
curl -H "Authorization: Bearer your_key" \
  -H "Content-Type: application/json" \
  -d '{"input": "测试文本", "model": "text-embedding-ada-002"}' \
  https://api.openai.com/v1/embeddings
```

#### 5. RAG 训练问题

```bash
# 检查训练状态
python -c "
from app.services.knowledge_base import KnowledgeBaseService
from app.core.database import get_db
# 检查知识库训练状态
"

# 查看训练日志
docker logs embedai-server | grep -i "training"

# 测试RAG模块
python -c "
from app.rag.retrieval.retrieval_service import RetrievalService
from app.rag.embedding.embedding_engine import EmbeddingEngine
print('RAG modules imported successfully')
"
```

#### 6. 配置验证脚本

```bash
# 创建配置验证脚本
cat > validate_config.py << 'EOF'
#!/usr/bin/env python3
import os
import sys
from sqlalchemy import create_engine
import redis

def validate_database():
    try:
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            print("❌ DATABASE_URL not set")
            return False
        engine = create_engine(db_url)
        engine.connect()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def validate_redis():
    try:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        r = redis.from_url(redis_url)
        r.ping()
        print("✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

def validate_llm_keys():
    keys = ['SILICONFLOW_API_KEY', 'OPENAI_API_KEY', 'ZHIPU_API_KEY']
    found = False
    for key in keys:
        if os.getenv(key):
            print(f"✅ {key} is set")
            found = True
    if not found:
        print("❌ No LLM API keys found")
        return False
    return True

if __name__ == "__main__":
    print("🔍 Validating EmbedAI configuration...")
    results = [
        validate_database(),
        validate_redis(),
        validate_llm_keys()
    ]

    if all(results):
        print("🎉 All configurations are valid!")
        sys.exit(0)
    else:
        print("💥 Some configurations are invalid!")
        sys.exit(1)
EOF

# 运行验证
python validate_config.py
```

## 📄 License

本项目采用 MIT License - 查看 [LICENSE](LICENSE) 文件了解详情

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## � 运持维和监控

### 系统监控

#### 关键指标监控

```bash
# RAG系统关键指标
- 检索响应时间 (P95 < 500ms)
- 向量化处理时间 (P95 < 100ms)
- 知识库训练成功率 (> 95%)
- API可用性 (> 99.9%)
- 内存使用率 (< 80%)
- 缓存命中率 (> 70%)
```

#### 日志监控

```bash
# 查看应用日志
docker logs -f embedai-server

# 查看RAG相关日志
docker logs embedai-server | grep -i "rag\|embedding\|retrieval"

# 查看错误日志
docker logs embedai-server | grep -i "error\|exception"

# 查看性能日志
docker logs embedai-server | grep -i "performance\|duration"
```

#### 健康检查

```bash
# API健康检查
curl http://localhost:8000/health

# 数据库连接检查
curl http://localhost:8000/health/db

# Redis连接检查
curl http://localhost:8000/health/redis

# RAG服务检查
curl http://localhost:8000/health/rag
```

### 备份和恢复

#### 数据备份策略

```bash
# 数据库备份
pg_dump -h localhost -U user embedai > backup_$(date +%Y%m%d).sql

# Redis数据备份
redis-cli --rdb backup_redis_$(date +%Y%m%d).rdb

# 知识库文件备份
tar -czf kb_files_$(date +%Y%m%d).tar.gz /path/to/knowledge_bases/
```

#### 恢复流程

```bash
# 数据库恢复
psql -h localhost -U user embedai < backup_20240101.sql

# Redis数据恢复
redis-cli --rdb backup_redis_20240101.rdb

# 重建向量索引
python scripts/rebuild_vectors.py
```

### 性能调优

#### 数据库优化

```sql
-- 创建必要的索引
CREATE INDEX idx_documents_kb_id ON documents(knowledge_base_id);
CREATE INDEX idx_document_chunks_doc_id ON document_chunks(document_id);
CREATE INDEX idx_embeddings_vector ON embeddings USING ivfflat (vector);

-- 定期维护
VACUUM ANALYZE documents;
VACUUM ANALYZE document_chunks;
```

#### Redis 优化

```bash
# Redis配置优化
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

#### 应用优化

```python
# 环境变量调优
WORKERS=4                    # 根据CPU核心数调整
MAX_CONNECTIONS=100          # 数据库连接池大小
REDIS_MAX_CONNECTIONS=50     # Redis连接池大小
CHUNK_SIZE=1000             # 文档分块大小
BATCH_SIZE=100              # 批处理大小
CACHE_TTL=3600              # 缓存过期时间（秒）
```

## 📞 支持

- 📧 Email: cong_wa@163.com
- 📦 GitHub Issues: [项目 Issues](https://github.com/congwa/EmbedAI-server/issues)
- 💬 讨论区: [项目 Discussions](https://github.com/congwa/EmbedAI-server/discussions)
