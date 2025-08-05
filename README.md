# EmbedAI Server - 智能知识库助手系统

企业级AI知识管理与服务系统，基于图数据库和大型语言模型，提供高性能的知识检索、智能问答和知识管理功能。

## 🌟 核心特性

### 📊 多租户知识管理
- **知识库隔离**：每个用户可创建和管理多个独立知识库
- **权限控制**：细粒度的用户权限管理（读/写/管理/所有者）
- **多用户协作**：支持知识库多用户共享与协作

### 🤖 先进AI技术
- **图数据库+向量数据库**：结合Neo4j图数据库和向量数据库
- **智能实体识别**：基于LLM的实体抽取和关系分析
- **多跳查询**：支持复杂关系的图遍历检索
- **重排序优化**：使用重排序模型提升结果准确性

### 📁 多格式文档处理
- **丰富文档类型**：PDF、Word、Excel、TXT、Markdown、HTML
- **智能分段**：基于语义的内容分块和重叠处理
- **元数据提取**：自动提取文档标题、关键词等元数据
- **OCR支持**：图片和扫描文档的文字识别

### 💬 智能问答系统
- **上下文问答**：基于整个知识库的智能回复
- **实时对话**：WebSocket支持的实时聊天
- **成本计算**：精确的Token使用和费用计算
- **防刷机制**：完善的访问频率控制和防滥用保护

## 🏗️ 技术架构

### 系统架构
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   Redis/Queue    │    │   Neo4j         │
│   API Server    │───→│   Async Tasks    │───→│   Graph DB      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                      │                      │
         ↓                      ↓                      ↓
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │   LLM Service    │    │   Vector Search │
│   Metadata      │    │   SiliconFlow    │    │   Embedding     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### 数据处理流程
1. **文档上传** → 解析文档内容
2. **内容分块** → 语义分段处理
3. **向量化** → 生成嵌入向量
4. **实体识别** → 提取实体和关系
5. **图存储** → 存储到Neo4j图数据库
6. **知识检索** → 图遍历+向量检索
7. **智能回答** → LLM生成回复

## 🚀 快速开始

### 环境要求
- Python 3.10+
- PostgreSQL
- Redis
- Neo4j

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
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
ZHIPU_API_KEY=your_api_key
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

### Docker部署

#### 1. 快速部署
```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

#### 2. 自定义部署
```bash
# 构建镜像
docker build -t embedai-server .

# 运行容器
docker run -d \
  --name embedai-server \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e NEO4J_URI=bolt://... \
  -e ZHIPU_API_KEY=your_key \
  embedai-server
```

### API文档
启动服务后访问：
- Swagger文档: http://localhost:8000/docs
- ReDoc文档: http://localhost:8000/redoc

## 📚 API使用指南

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

### 智能问答
```bash
# REST API问答
POST /api/v1/chat/completions
{
  "knowledge_base_id": "uuid",
  "messages": [
    {"role": "user", "content": "公司的请假流程是什么？"}
  ]
}

# WebSocket实时对话
ws://localhost:8000/ws/chat/{knowledge_base_id}
```

## 🧪 开发指南

### 项目结构
```
EmbedAI-server/
├── app/
│   ├── api/v1/          # API路由
│   ├── core/            # 核心配置
│   ├── models/          # 数据库模型
│   ├── schemas/         # 数据验证
│   └── services/        # 业务逻辑
├── _rag/                # RAG引擎
│   ├── retrieval/       # 检索模块
│   ├── extractor/       # 文档提取
│   └── docstore/        # 文档存储
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

#### 支持的LLM服务
- **SiliconFlow** (默认): 免费额度充足，支持Qwen系列模型
- **OpenAI**: GPT-3.5, GPT-4等
- **Zhipu**: 中文优化，适合国内使用

#### 配置示例
```python
# 修改 app/core/config.py
DEFAULT_LLM_MODEL = "Qwen/Qwen2.5-7B-Instruct"
DEFAULT_API_BASE = "https://api.siliconflow.cn/v1"
DEFAULT_API_KEY = "sk-xxx"
```

## 📊 性能优化

### 缓存策略
- **Redis**: 缓存常用查询结果
- **向量缓存**: 避免重复向量化处理
- **知识图谱**: Neo4j查询结果缓存

### 扩展建议
- **水平扩展**: 使用负载均衡部署多台实例
- **数据库分片**: 按知识库或用户分片
- **缓存预热**: 预加载热门数据

## 🔄 配套项目

### SDK和前端
- **[EmbedAI-sdk H5端sdk](./frontend/sdk/)**: 移动端SDK，快速集成到移动应用
- **[EmbedAI-admin 后台管理端](./frontend/admin/)**: 管理后台，监控和配置管理

### 客户端示例
```javascript
// JavaScript SDK示例
const sdk = new EmbedAI({
  baseURL: 'http://localhost:8000',
  token: 'your_jwt_token'
});

// 获取知识库列表
await sdk.getKnowledgeBases();

// 上传文档并训练
await sdk.uploadDocument(kbId, file);

// 智能问答
await sdk.chat(kbId, '问题内容');
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

#### 2. Neo4j连接问题
```bash
# 检查Neo4j状态
curl -H "Accept: application/json" -H "Content-Type: application/json" \
  -u "neo4j:password" \
  http://localhost:7474/db/data/
```

#### 3. Redis连接问题
```bash
# 检查Redis连接
redis-cli ping
# 应返回 PONG
```

#### 4. 模型调用失败
```bash
# 检查API密钥
curl -H "Authorization: Bearer your_key" \
  https://api.siliconflow.cn/v1/models
```

## 📄 License

本项目采用 MIT License - 查看 [LICENSE](LICENSE) 文件了解详情

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📞 支持

- 📧 Email: cong_wa@163.com
- 📦 GitHub Issues: [项目Issues](https://github.com/congwa/EmbedAI-server/issues)
- 💬 讨论区: [项目Discussions](https://github.com/congwa/EmbedAI-server/discussions)