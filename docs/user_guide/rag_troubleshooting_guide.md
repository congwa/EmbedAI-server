# RAG功能故障排除指南

## 概述

本指南提供了RAG（Retrieval-Augmented Generation）功能常见问题的诊断和解决方案，帮助您快速定位和解决问题。

## 故障诊断流程

### 1. 问题分类

根据问题类型进行初步分类：

- **文档处理问题**: 文档上传、解析、分块失败
- **向量化问题**: 向量生成、存储失败
- **检索问题**: 查询无结果、结果不准确
- **性能问题**: 响应慢、内存占用高
- **配置问题**: 配置错误、服务无法启动

### 2. 日志检查

首先检查相关日志：

```bash
# 查看RAG相关日志
tail -f logs/rag.log

# 查看应用日志
tail -f logs/app.log

# 查看错误日志
grep -i error logs/rag.log | tail -20
```

### 3. 系统状态检查

```python
# 检查系统状态
from app.services.knowledge_base import KnowledgeBaseService

kb_service = KnowledgeBaseService(db_session)

# 检查向量数据库连接
status = await kb_service.check_vector_db_status()
print(f"向量数据库状态: {status}")

# 检查缓存连接
cache_status = await kb_service.check_cache_status()
print(f"缓存状态: {cache_status}")
```

## 常见问题及解决方案

### 文档处理问题

#### 问题1: 文档上传失败

**症状**:
```
DocumentProcessingError: 无法处理文档 example.pdf
```

**可能原因**:
- 文档格式不支持
- 文档损坏或加密
- 文件大小超限
- 权限不足

**解决方案**:

```python
# 1. 检查文档格式
supported_formats = [".pdf", ".docx", ".xlsx", ".md", ".html", ".txt"]
file_ext = os.path.splitext(filename)[1].lower()
if file_ext not in supported_formats:
    print(f"不支持的文档格式: {file_ext}")

# 2. 检查文件大小
max_size = 50 * 1024 * 1024  # 50MB
file_size = os.path.getsize(file_path)
if file_size > max_size:
    print(f"文件过大: {file_size} bytes")

# 3. 检查文件权限
if not os.access(file_path, os.R_OK):
    print("文件读取权限不足")

# 4. 验证文档完整性
try:
    with open(file_path, 'rb') as f:
        # 尝试读取文件头
        header = f.read(1024)
        if not header:
            print("文档为空或损坏")
except Exception as e:
    print(f"文档读取失败: {e}")
```

#### 问题2: PDF文档解析失败

**症状**:
```
PDFExtractionError: 无法提取PDF内容
```

**解决方案**:

```python
# 检查PDF文档
import PyPDF2
from app.rag.extractor.pdf_extractor import PDFExtractor

try:
    extractor = PDFExtractor()
    content = await extractor.extract(file_path)
    print(f"提取内容长度: {len(content)}")
except Exception as e:
    print(f"PDF提取失败: {e}")
    
    # 尝试使用OCR
    try:
        content = await extractor.extract_with_ocr(file_path)
        print("OCR提取成功")
    except Exception as ocr_error:
        print(f"OCR提取也失败: {ocr_error}")
```

#### 问题3: 文本分块异常

**症状**:
```
TextSplittingError: 分块处理失败
```

**解决方案**:

```python
from app.rag.splitter.text_splitter import TextSplitter

# 检查文本内容
if not text or len(text.strip()) == 0:
    print("文本内容为空")

# 调整分块参数
splitter = TextSplitter(
    chunk_size=500,  # 减小分块大小
    chunk_overlap=50,  # 减小重叠
    strategy="fixed"  # 使用简单策略
)

try:
    chunks = await splitter.split_text(text)
    print(f"分块成功，共{len(chunks)}块")
except Exception as e:
    print(f"分块失败: {e}")
```

### 向量化问题

#### 问题4: 向量化服务连接失败

**症状**:
```
EmbeddingError: 无法连接到向量化服务
```

**解决方案**:

```python
# 检查API配置
from app.core.config import settings

if settings.OPENAI_API_KEY:
    print("OpenAI API Key已配置")
    
    # 测试API连接
    import openai
    openai.api_key = settings.OPENAI_API_KEY
    
    try:
        response = openai.Embedding.create(
            input="测试文本",
            model="text-embedding-ada-002"
        )
        print("OpenAI API连接正常")
    except Exception as e:
        print(f"OpenAI API连接失败: {e}")
else:
    print("未配置OpenAI API Key")

# 检查本地模型
try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embedding = model.encode("测试文本")
    print(f"本地模型正常，向量维度: {len(embedding)}")
except Exception as e:
    print(f"本地模型加载失败: {e}")
```

#### 问题5: 向量维度不匹配

**症状**:
```
VectorDimensionError: 向量维度不匹配
```

**解决方案**:

```python
# 检查向量维度配置
from app.rag.embedding.embedding_engine import EmbeddingEngine

engine = EmbeddingEngine(llm_config)
test_embedding = await engine.embed_query("测试")
print(f"实际向量维度: {len(test_embedding)}")

# 检查向量数据库配置
if settings.VECTOR_DB_TYPE == "qdrant":
    expected_dim = settings.QDRANT_VECTOR_SIZE
    if len(test_embedding) != expected_dim:
        print(f"维度不匹配: 期望{expected_dim}, 实际{len(test_embedding)}")
        
        # 更新配置
        settings.QDRANT_VECTOR_SIZE = len(test_embedding)
```

### 向量存储问题

#### 问题6: Chroma数据库连接失败

**症状**:
```
ChromaConnectionError: 无法连接到Chroma数据库
```

**解决方案**:

```python
import chromadb
from chromadb.config import Settings as ChromaSettings

try:
    # 检查Chroma配置
    if settings.CHROMA_HOST and settings.CHROMA_PORT:
        # 远程连接
        client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT
        )
    else:
        # 本地连接
        client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIRECTORY
        )
    
    # 测试连接
    collections = client.list_collections()
    print(f"Chroma连接成功，集合数量: {len(collections)}")
    
except Exception as e:
    print(f"Chroma连接失败: {e}")
    
    # 检查目录权限
    import os
    if not os.path.exists(settings.CHROMA_PERSIST_DIRECTORY):
        os.makedirs(settings.CHROMA_PERSIST_DIRECTORY)
        print(f"创建Chroma目录: {settings.CHROMA_PERSIST_DIRECTORY}")
```

#### 问题7: Qdrant数据库连接失败

**症状**:
```
QdrantConnectionError: 无法连接到Qdrant数据库
```

**解决方案**:

```python
from qdrant_client import QdrantClient
from qdrant_client.http import models

try:
    # 创建Qdrant客户端
    client = QdrantClient(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT,
        api_key=settings.QDRANT_API_KEY,
        https=settings.QDRANT_HTTPS
    )
    
    # 测试连接
    info = client.get_cluster_info()
    print(f"Qdrant连接成功: {info}")
    
except Exception as e:
    print(f"Qdrant连接失败: {e}")
    
    # 检查网络连接
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((settings.QDRANT_HOST, settings.QDRANT_PORT))
        if result == 0:
            print("网络连接正常")
        else:
            print("网络连接失败")
        sock.close()
    except Exception as net_error:
        print(f"网络检查失败: {net_error}")
```

### 检索问题

#### 问题8: 查询无结果

**症状**:
查询知识库时返回空结果

**解决方案**:

```python
# 1. 检查索引是否存在
from app.rag.retrieval.retrieval_service import RetrievalService

service = RetrievalService(db_session)
index_status = await service.check_index_status(knowledge_base.id)
print(f"索引状态: {index_status}")

if not index_status['exists']:
    print("索引不存在，需要重新训练")
    await kb_service.train_rag(knowledge_base.id, llm_config, user_id)

# 2. 降低相似度阈值
results = await service.query(
    knowledge_base=knowledge_base,
    query=query,
    llm_config=llm_config,
    score_threshold=0.3,  # 降低阈值
    top_k=20  # 增加返回数量
)

# 3. 尝试不同的检索方法
methods = ["semantic_search", "keyword_search", "hybrid_search"]
for method in methods:
    results = await service.query(
        knowledge_base=knowledge_base,
        query=query,
        llm_config=llm_config,
        method=method,
        top_k=10
    )
    print(f"{method}: {len(results)}个结果")

# 4. 检查查询向量
query_embedding = await embedding_engine.embed_query(query)
print(f"查询向量维度: {len(query_embedding)}")
print(f"查询向量范数: {sum(x*x for x in query_embedding)**0.5}")
```

#### 问题9: 检索结果不准确

**症状**:
返回的结果与查询内容不相关

**解决方案**:

```python
# 1. 启用重排序
results = await service.query(
    knowledge_base=knowledge_base,
    query=query,
    llm_config=llm_config,
    use_rerank=True,
    rerank_mode="weighted_score"
)

# 2. 调整检索参数
results = await service.query(
    knowledge_base=knowledge_base,
    query=query,
    llm_config=llm_config,
    method="hybrid_search",
    semantic_weight=0.8,  # 增加语义权重
    keyword_weight=0.2
)

# 3. 检查文档质量
chunks = await service.get_document_chunks(knowledge_base.id)
for chunk in chunks[:5]:
    print(f"分块内容: {chunk.content[:100]}...")
    print(f"分块长度: {len(chunk.content)}")

# 4. 重新训练特定文档
await kb_service.retrain_documents(
    knowledge_base.id,
    document_ids=[doc.id],
    llm_config=llm_config
)
```

### 性能问题

#### 问题10: 查询响应慢

**症状**:
查询响应时间超过5秒

**解决方案**:

```python
import time
from app.rag.retrieval.query_cache import QueryCache

# 1. 启用缓存
results = await service.query(
    knowledge_base=knowledge_base,
    query=query,
    llm_config=llm_config,
    use_cache=True
)

# 2. 减少返回结果数量
results = await service.query(
    knowledge_base=knowledge_base,
    query=query,
    llm_config=llm_config,
    top_k=5  # 减少到5个
)

# 3. 性能分析
start_time = time.time()

# 向量化时间
embed_start = time.time()
query_embedding = await embedding_engine.embed_query(query)
embed_time = time.time() - embed_start

# 检索时间
search_start = time.time()
raw_results = await vector_store.similarity_search(query_embedding, k=10)
search_time = time.time() - search_start

total_time = time.time() - start_time

print(f"向量化时间: {embed_time:.2f}s")
print(f"检索时间: {search_time:.2f}s")
print(f"总时间: {total_time:.2f}s")

# 4. 优化向量数据库
if settings.VECTOR_DB_TYPE == "qdrant":
    # 优化Qdrant索引
    await vector_store.optimize_index()
```

#### 问题11: 内存占用过高

**症状**:
系统内存使用率超过80%

**解决方案**:

```python
import psutil
import gc

# 1. 检查内存使用
process = psutil.Process()
memory_info = process.memory_info()
print(f"内存使用: {memory_info.rss / 1024 / 1024:.2f} MB")

# 2. 清理缓存
await QueryCache.clear_all_cache()
gc.collect()

# 3. 减少批处理大小
embedding_engine.batch_size = 50  # 减少批处理大小

# 4. 限制并发数
settings.RAG_MAX_WORKERS = 2  # 减少并发数

# 5. 监控内存使用
def monitor_memory():
    memory_percent = psutil.virtual_memory().percent
    if memory_percent > 80:
        print(f"内存使用率过高: {memory_percent}%")
        # 触发清理
        gc.collect()
        
# 定期检查
import asyncio
asyncio.create_task(monitor_memory())
```

### 配置问题

#### 问题12: 配置文件错误

**症状**:
```
ConfigurationError: 配置验证失败
```

**解决方案**:

```python
from app.core.config import Settings
from pydantic import ValidationError

try:
    settings = Settings()
    print("配置验证通过")
except ValidationError as e:
    print(f"配置错误: {e}")
    
    # 检查必需的环境变量
    required_vars = [
        "VECTOR_DB_TYPE",
        "RAG_CHUNK_SIZE",
        "RAG_EMBEDDING_BATCH_SIZE"
    ]
    
    import os
    for var in required_vars:
        if var not in os.environ:
            print(f"缺少环境变量: {var}")

# 验证配置值
def validate_config():
    if settings.RAG_CHUNK_SIZE <= 0:
        raise ValueError("RAG_CHUNK_SIZE必须大于0")
    
    if settings.RAG_CHUNK_OVERLAP >= settings.RAG_CHUNK_SIZE:
        raise ValueError("RAG_CHUNK_OVERLAP必须小于RAG_CHUNK_SIZE")
    
    if settings.VECTOR_DB_TYPE not in ["chroma", "qdrant"]:
        raise ValueError("不支持的向量数据库类型")

validate_config()
```

#### 问题13: 服务启动失败

**症状**:
```
ServiceStartupError: RAG服务启动失败
```

**解决方案**:

```python
# 1. 检查依赖服务
async def check_dependencies():
    # 检查数据库连接
    try:
        from app.core.database import get_db
        db = next(get_db())
        print("数据库连接正常")
    except Exception as e:
        print(f"数据库连接失败: {e}")
    
    # 检查Redis连接
    try:
        from app.core.redis import redis_manager
        await redis_manager.ping()
        print("Redis连接正常")
    except Exception as e:
        print(f"Redis连接失败: {e}")
    
    # 检查向量数据库
    try:
        from app.rag.datasource.vdb.vector_factory import VectorStoreFactory
        vector_store = VectorStoreFactory.create_vector_store(
            settings.VECTOR_DB_TYPE,
            {}
        )
        await vector_store.health_check()
        print("向量数据库连接正常")
    except Exception as e:
        print(f"向量数据库连接失败: {e}")

await check_dependencies()

# 2. 检查文件权限
import os
directories = [
    settings.CHROMA_PERSIST_DIRECTORY,
    "./logs",
    "./data"
]

for directory in directories:
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        print(f"创建目录: {directory}")
    
    if not os.access(directory, os.W_OK):
        print(f"目录写权限不足: {directory}")
```

## 诊断工具

### 系统诊断脚本

```python
# scripts/diagnose_rag.py
import asyncio
import sys
from app.core.config import settings
from app.services.knowledge_base import KnowledgeBaseService

async def diagnose_system():
    """系统诊断"""
    print("=== RAG系统诊断 ===")
    
    # 1. 配置检查
    print("\n1. 配置检查:")
    print(f"向量数据库类型: {settings.VECTOR_DB_TYPE}")
    print(f"分块大小: {settings.RAG_CHUNK_SIZE}")
    print(f"批处理大小: {settings.RAG_EMBEDDING_BATCH_SIZE}")
    
    # 2. 服务状态检查
    print("\n2. 服务状态检查:")
    try:
        kb_service = KnowledgeBaseService(db_session)
        
        # 检查向量数据库
        vector_status = await kb_service.check_vector_db_status()
        print(f"向量数据库: {'正常' if vector_status else '异常'}")
        
        # 检查缓存
        cache_status = await kb_service.check_cache_status()
        print(f"缓存服务: {'正常' if cache_status else '异常'}")
        
    except Exception as e:
        print(f"服务检查失败: {e}")
    
    # 3. 性能检查
    print("\n3. 性能检查:")
    import psutil
    
    cpu_percent = psutil.cpu_percent(interval=1)
    memory_percent = psutil.virtual_memory().percent
    disk_percent = psutil.disk_usage('/').percent
    
    print(f"CPU使用率: {cpu_percent}%")
    print(f"内存使用率: {memory_percent}%")
    print(f"磁盘使用率: {disk_percent}%")
    
    # 4. 功能测试
    print("\n4. 功能测试:")
    try:
        # 测试向量化
        from app.rag.embedding.embedding_engine import EmbeddingEngine
        from app.models.llm_config import LLMConfig
        
        llm_config = LLMConfig(embeddings={"provider": "test"})
        engine = EmbeddingEngine(llm_config)
        
        test_embedding = await engine.embed_query("测试文本")
        print(f"向量化测试: 成功 (维度: {len(test_embedding)})")
        
    except Exception as e:
        print(f"向量化测试: 失败 ({e})")

if __name__ == "__main__":
    asyncio.run(diagnose_system())
```

### 性能分析工具

```python
# scripts/performance_analysis.py
import time
import asyncio
from app.rag.retrieval.retrieval_service import RetrievalService

async def analyze_performance(knowledge_base_id: int, queries: list):
    """性能分析"""
    service = RetrievalService(db_session)
    
    results = []
    for query in queries:
        start_time = time.time()
        
        try:
            search_results = await service.query(
                knowledge_base_id=knowledge_base_id,
                query=query,
                top_k=10
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            results.append({
                "query": query,
                "response_time": response_time,
                "result_count": len(search_results),
                "status": "success"
            })
            
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            
            results.append({
                "query": query,
                "response_time": response_time,
                "result_count": 0,
                "status": "error",
                "error": str(e)
            })
    
    # 统计分析
    successful_queries = [r for r in results if r["status"] == "success"]
    if successful_queries:
        avg_response_time = sum(r["response_time"] for r in successful_queries) / len(successful_queries)
        max_response_time = max(r["response_time"] for r in successful_queries)
        min_response_time = min(r["response_time"] for r in successful_queries)
        
        print(f"成功查询数: {len(successful_queries)}/{len(queries)}")
        print(f"平均响应时间: {avg_response_time:.2f}s")
        print(f"最大响应时间: {max_response_time:.2f}s")
        print(f"最小响应时间: {min_response_time:.2f}s")
    
    return results
```

## 监控和告警

### 健康检查端点

```python
# app/api/v1/health.py
from fastapi import APIRouter, Depends
from app.services.knowledge_base import KnowledgeBaseService

router = APIRouter()

@router.get("/health/rag")
async def rag_health_check(
    kb_service: KnowledgeBaseService = Depends()
):
    """RAG功能健康检查"""
    health_status = {
        "status": "healthy",
        "checks": {}
    }
    
    try:
        # 检查向量数据库
        vector_db_status = await kb_service.check_vector_db_status()
        health_status["checks"]["vector_db"] = "healthy" if vector_db_status else "unhealthy"
        
        # 检查缓存
        cache_status = await kb_service.check_cache_status()
        health_status["checks"]["cache"] = "healthy" if cache_status else "unhealthy"
        
        # 检查嵌入服务
        embedding_status = await kb_service.check_embedding_status()
        health_status["checks"]["embedding"] = "healthy" if embedding_status else "unhealthy"
        
        # 总体状态
        if not all(status == "healthy" for status in health_status["checks"].values()):
            health_status["status"] = "unhealthy"
            
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
    
    return health_status
```

### 告警配置

```python
# app/utils/alerts.py
import smtplib
from email.mime.text import MIMEText
from app.core.config import settings

class AlertManager:
    @staticmethod
    async def send_alert(title: str, message: str, level: str = "warning"):
        """发送告警"""
        if level == "critical":
            # 发送邮件告警
            await AlertManager._send_email_alert(title, message)
        
        # 记录告警日志
        from app.core.logger import Logger
        Logger.warning(f"[ALERT] {title}: {message}")
    
    @staticmethod
    async def _send_email_alert(title: str, message: str):
        """发送邮件告警"""
        if not settings.ALERT_EMAIL_ENABLED:
            return
        
        try:
            msg = MIMEText(message)
            msg['Subject'] = f"[RAG系统告警] {title}"
            msg['From'] = settings.ALERT_EMAIL_FROM
            msg['To'] = settings.ALERT_EMAIL_TO
            
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            from app.core.logger import Logger
            Logger.error(f"邮件告警发送失败: {e}")

# 使用示例
await AlertManager.send_alert(
    title="向量数据库连接失败",
    message="Qdrant数据库连接超时，请检查网络和服务状态",
    level="critical"
)
```

## 预防措施

### 1. 定期维护

```bash
# 定期清理脚本
#!/bin/bash
# scripts/maintenance.sh

echo "开始RAG系统维护..."

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
# 优化所有知识库的索引
"

# 清理日志文件
find ./logs -name "*.log" -mtime +30 -delete

echo "维护完成"
```

### 2. 监控脚本

```python
# scripts/monitor.py
import asyncio
import time
from app.utils.alerts import AlertManager

async def monitor_system():
    """系统监控"""
    while True:
        try:
            # 检查内存使用
            import psutil
            memory_percent = psutil.virtual_memory().percent
            if memory_percent > 85:
                await AlertManager.send_alert(
                    "内存使用率过高",
                    f"当前内存使用率: {memory_percent}%",
                    "warning"
                )
            
            # 检查磁盘空间
            disk_percent = psutil.disk_usage('/').percent
            if disk_percent > 90:
                await AlertManager.send_alert(
                    "磁盘空间不足",
                    f"当前磁盘使用率: {disk_percent}%",
                    "critical"
                )
            
            # 检查服务状态
            from app.services.knowledge_base import KnowledgeBaseService
            kb_service = KnowledgeBaseService(db_session)
            
            if not await kb_service.check_vector_db_status():
                await AlertManager.send_alert(
                    "向量数据库异常",
                    "向量数据库连接失败",
                    "critical"
                )
            
        except Exception as e:
            await AlertManager.send_alert(
                "监控脚本异常",
                f"监控脚本执行失败: {e}",
                "warning"
            )
        
        # 每5分钟检查一次
        await asyncio.sleep(300)

if __name__ == "__main__":
    asyncio.run(monitor_system())
```

### 3. 备份策略

```python
# scripts/backup.py
import os
import shutil
import datetime
from app.core.config import settings

def backup_vector_db():
    """备份向量数据库"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if settings.VECTOR_DB_TYPE == "chroma":
        source_dir = settings.CHROMA_PERSIST_DIRECTORY
        backup_dir = f"./backups/chroma_{timestamp}"
        
        if os.path.exists(source_dir):
            shutil.copytree(source_dir, backup_dir)
            print(f"Chroma数据库备份完成: {backup_dir}")
    
    elif settings.VECTOR_DB_TYPE == "qdrant":
        # Qdrant备份需要使用API
        print("Qdrant备份需要使用专用工具")

def cleanup_old_backups(days=7):
    """清理旧备份"""
    backup_dir = "./backups"
    if not os.path.exists(backup_dir):
        return
    
    cutoff_time = datetime.datetime.now() - datetime.timedelta(days=days)
    
    for item in os.listdir(backup_dir):
        item_path = os.path.join(backup_dir, item)
        if os.path.isdir(item_path):
            item_time = datetime.datetime.fromtimestamp(os.path.getctime(item_path))
            if item_time < cutoff_time:
                shutil.rmtree(item_path)
                print(f"删除旧备份: {item_path}")

if __name__ == "__main__":
    backup_vector_db()
    cleanup_old_backups()
```

---

*本故障排除指南涵盖了RAG功能的常见问题和解决方案，建议定期更新和完善。*