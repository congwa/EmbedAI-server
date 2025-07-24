# RAG知识库训练API文档

## 简介

RAG知识库训练API提供了一组完整的接口，用于管理和使用基于检索增强生成（Retrieval-Augmented Generation，RAG）的知识库。这些API支持多种文档格式处理、智能向量化、多种检索方式和结果优化等功能。

### 主要功能

- **知识库管理**: 创建、更新、删除知识库
- **文档管理**: 上传、处理多种格式文档（PDF、Word、Excel、Markdown、HTML、TXT）
- **RAG训练**: 文档解析、分块、向量化、索引构建
- **智能检索**: 语义搜索、关键词搜索、混合搜索
- **结果优化**: 多种重排序算法
- **性能优化**: 缓存管理、批量处理
- **监控管理**: 训练状态、性能统计、日志查看

### API版本

当前API版本：`v1`

### 基础URL

```
https://your-domain.com/api/v1
```

### 认证方式

所有API请求都需要在请求头中包含有效的认证令牌：

```http
Authorization: Bearer <your-access-token>
```

## API端点

### 知识库管理

#### 创建知识库

```
POST /api/v1/admin/knowledge-bases
```

创建一个新的知识库。

**请求体**：
```json
{
  "name": "测试知识库",
  "domain": "测试领域",
  "example_queries": ["问题1", "问题2"],
  "entity_types": ["实体1", "实体2"],
  "llm_config": {
    "llm": {
      "model": "Qwen/Qwen2.5-7B-Instruct",
      "base_url": "https://api.siliconflow.cn/v1",
      "api_key": "your-api-key"
    },
    "embeddings": {
      "model": "BAAI/bge-m3",
      "base_url": "https://api.siliconflow.cn/v1",
      "api_key": "your-api-key",
      "embedding_dim": 1024
    }
  }
}
```

**响应**：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "name": "测试知识库",
    "domain": "测试领域",
    "example_queries": ["问题1", "问题2"],
    "entity_types": ["实体1", "实体2"],
    "owner_id": 1,
    "training_status": "init",
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z"
  }
}
```

#### 获取知识库详情

```
GET /api/v1/admin/knowledge-bases/{kb_id}
```

获取知识库的详细信息。

**路径参数**：
- `kb_id`：知识库ID

**响应**：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "name": "测试知识库",
    "domain": "测试领域",
    "example_queries": ["问题1", "问题2"],
    "entity_types": ["实体1", "实体2"],
    "owner_id": 1,
    "training_status": "trained",
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z",
    "members": [
      {
        "id": 1,
        "email": "user@example.com",
        "permission": "owner",
        "is_owner": true,
        "is_admin": false
      }
    ]
  }
}
```

#### 更新知识库

```
PUT /api/v1/admin/knowledge-bases/{kb_id}
```

更新知识库的信息。

**路径参数**：
- `kb_id`：知识库ID

**请求体**：
```json
{
  "name": "更新后的知识库名称",
  "domain": "更新后的领域",
  "example_queries": ["新问题1", "新问题2"],
  "entity_types": ["新实体1", "新实体2"]
}
```

**响应**：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "name": "更新后的知识库名称",
    "domain": "更新后的领域",
    "example_queries": ["新问题1", "新问题2"],
    "entity_types": ["新实体1", "新实体2"],
    "owner_id": 1,
    "training_status": "trained",
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z"
  }
}
```

### 文档管理

#### 上传文档

```
POST /api/v1/admin/knowledge-bases/{kb_id}/documents
```

上传文档到知识库。

**路径参数**：
- `kb_id`：知识库ID

**请求体**：
```
multipart/form-data
- file: 文件
- title: 文档标题
- source_url: 文档来源URL（可选）
```

**响应**：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "title": "文档标题",
    "source_url": "https://example.com/doc",
    "knowledge_base_id": 1,
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z"
  }
}
```

#### 获取知识库文档列表

```
GET /api/v1/admin/knowledge-bases/{kb_id}/documents
```

获取知识库的文档列表。

**路径参数**：
- `kb_id`：知识库ID

**查询参数**：
- `page`：页码，默认为1
- `page_size`：每页数量，默认为10

**响应**：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "title": "文档标题",
        "source_url": "https://example.com/doc",
        "knowledge_base_id": 1,
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 10
  }
}
```

### 知识库训练

#### 训练知识库

```
POST /api/v1/admin/knowledge-bases/{kb_id}/train
```

训练知识库。

**路径参数**：
- `kb_id`：知识库ID

**响应**：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "name": "测试知识库",
    "training_status": "training",
    "training_started_at": "2023-01-01T00:00:00Z"
  }
}
```

#### 获取训练队列状态

```
GET /api/v1/admin/knowledge-bases/training-queue
```

获取训练队列状态。

**响应**：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "training": {
      "id": 1,
      "name": "测试知识库",
      "started_at": "2023-01-01T00:00:00Z"
    },
    "queue": [
      {
        "id": 2,
        "name": "测试知识库2",
        "queued_at": "2023-01-01T00:00:00Z"
      }
    ],
    "queue_length": 1
  }
}
```

### 知识库查询

#### 查询知识库

```
POST /api/v1/admin/knowledge-bases/{kb_id}/query
```

查询知识库。

**路径参数**：
- `kb_id`：知识库ID

**请求体**：
```json
{
  "query": "查询内容",
  "method": "hybrid_search",
  "top_k": 5,
  "use_rerank": true,
  "rerank_mode": "weighted_score"
}
```

**响应**：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "query": "查询内容",
    "results": [
      {
        "content": "文档内容片段",
        "score": 0.95,
        "metadata": {
          "document_id": 1,
          "chunk_id": 1
        },
        "document": {
          "id": 1,
          "title": "文档标题",
          "source_url": "https://example.com/doc"
        },
        "chunk": {
          "id": 1,
          "index": 0
        }
      }
    ],
    "doc_metadata": {
      "kb_id": 1,
      "top_k": 5,
      "method": "hybrid_search",
      "use_rerank": true,
      "rerank_mode": "weighted_score",
      "user_type": "official",
      "user_id": 1
    }
  }
}
```

## 错误码

| 错误码 | 描述 |
| --- | --- |
| 0 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## 权限要求

| API | 所需权限 |
| --- | --- |
| 创建知识库 | 登录用户 |
| 获取知识库详情 | VIEWER |
| 更新知识库 | EDITOR |
| 上传文档 | EDITOR |
| 获取知识库文档列表 | VIEWER |
| 训练知识库 | EDITOR |
| 获取训练队列状态 | ADMIN |
| 查询知识库 | VIEWER |

### RAG训练管理

#### 获取训练状态

```http
GET /api/v1/admin/knowledge-bases/{kb_id}/training-status
```

获取知识库的详细训练状态。

**路径参数**：

- `kb_id`：知识库ID

**响应**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "knowledge_base_id": 1,
    "status": "training",
    "progress": 65,
    "current_step": "向量化处理",
    "processed_documents": 2,
    "total_documents": 3,
    "processed_chunks": 25,
    "total_chunks": 40,
    "training_started_at": "2023-01-01T00:00:00Z",
    "estimated_completion": "2023-01-01T00:08:00Z",
    "error_message": null
  }
}
```

#### 停止训练

```http
POST /api/v1/admin/knowledge-bases/{kb_id}/stop-training
```

停止正在进行的训练任务。

**路径参数**：

- `kb_id`：知识库ID

**响应**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "knowledge_base_id": 1,
    "status": "stopped",
    "stopped_at": "2023-01-01T00:05:00Z"
  }
}
```

### 高级检索功能

#### 语义搜索

```http
POST /api/v1/admin/knowledge-bases/{kb_id}/semantic-search
```

执行纯语义搜索。

**路径参数**：

- `kb_id`：知识库ID

**请求体**：

```json
{
  "query": "系统性能优化方法",
  "top_k": 10,
  "score_threshold": 0.6,
  "filters": {
    "document_ids": [1, 2, 3]
  }
}
```

**响应**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "query": "系统性能优化方法",
    "results": [
      {
        "content": "系统性能可以通过以下方法进行优化...",
        "score": 0.92,
        "document": {
          "id": 2,
          "title": "性能优化指南"
        },
        "chunk": {
          "id": 10,
          "index": 2
        }
      }
    ],
    "total_results": 8,
    "response_time": 180
  }
}
```

#### 关键词搜索

```http
POST /api/v1/admin/knowledge-bases/{kb_id}/keyword-search
```

执行关键词搜索。

**路径参数**：

- `kb_id`：知识库ID

**请求体**：

```json
{
  "query": "配置 参数 设置",
  "top_k": 10,
  "search_mode": "all",
  "boost_fields": {
    "title": 2.0,
    "content": 1.0
  }
}
```

**响应**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "query": "配置 参数 设置",
    "results": [
      {
        "content": "配置参数的设置方法如下...",
        "score": 0.88,
        "matched_keywords": ["配置", "参数", "设置"],
        "document": {
          "id": 1,
          "title": "配置管理手册"
        }
      }
    ],
    "total_results": 6,
    "response_time": 120
  }
}
```

### 缓存管理

#### 获取缓存统计

```http
GET /api/v1/admin/knowledge-bases/{kb_id}/cache/stats
```

获取知识库的缓存统计信息。

**路径参数**：

- `kb_id`：知识库ID

**响应**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "query_cache": {
      "total_entries": 150,
      "hit_count": 120,
      "miss_count": 30,
      "hit_rate": 0.8,
      "cache_size": "2.5MB"
    },
    "embedding_cache": {
      "total_entries": 500,
      "hit_count": 450,
      "miss_count": 50,
      "hit_rate": 0.9,
      "cache_size": "15.2MB"
    }
  }
}
```

#### 清理缓存

```http
DELETE /api/v1/admin/knowledge-bases/{kb_id}/cache
```

清理知识库的缓存数据。

**路径参数**：

- `kb_id`：知识库ID

**查询参数**：

- `cache_type`：缓存类型（query, embedding, all），默认为all

**响应**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "cleared_caches": ["query", "embedding"],
    "freed_memory": "17.7MB",
    "cleared_at": "2023-01-01T00:00:00Z"
  }
}
```

### 性能监控

#### 获取性能统计

```http
GET /api/v1/admin/knowledge-bases/{kb_id}/performance
```

获取知识库的性能统计信息。

**路径参数**：

- `kb_id`：知识库ID

**查询参数**：

- `time_range`：时间范围（1h, 24h, 7d, 30d），默认为24h

**响应**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "time_range": "24h",
    "query_stats": {
      "total_queries": 150,
      "avg_response_time": 250,
      "max_response_time": 800,
      "min_response_time": 100,
      "error_rate": 0.02
    },
    "cache_stats": {
      "query_cache_hit_rate": 0.8,
      "embedding_cache_hit_rate": 0.9
    },
    "resource_usage": {
      "memory_usage": "128MB",
      "cpu_usage": 0.15
    }
  }
}
```

### 系统健康检查

#### RAG系统健康检查

```http
GET /api/v1/admin/health/rag
```

检查RAG系统的健康状态。

**响应**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "status": "healthy",
    "timestamp": "2023-01-01T12:00:00Z",
    "checks": {
      "database": {
        "status": "healthy",
        "response_time": 10
      },
      "vector_database": {
        "status": "healthy",
        "response_time": 25
      },
      "cache": {
        "status": "healthy",
        "response_time": 5
      },
      "embedding_service": {
        "status": "healthy",
        "response_time": 150
      }
    }
  }
}
```

## 业务错误码

| 错误码 | 错误标识 | 描述 |
|--------|----------|------|
| 1001 | KNOWLEDGE_BASE_NOT_FOUND | 知识库不存在 |
| 1002 | DOCUMENT_NOT_FOUND | 文档不存在 |
| 1003 | TRAINING_IN_PROGRESS | 训练正在进行中 |
| 1004 | TRAINING_FAILED | 训练失败 |
| 1005 | UNSUPPORTED_FILE_FORMAT | 不支持的文件格式 |
| 1006 | FILE_TOO_LARGE | 文件过大 |
| 1007 | DOCUMENT_PROCESSING_FAILED | 文档处理失败 |
| 1008 | EMBEDDING_FAILED | 向量化失败 |
| 1009 | VECTOR_STORE_ERROR | 向量存储错误 |
| 1010 | QUERY_FAILED | 查询失败 |

## 使用示例

### Python客户端示例

```python
import requests

class RAGClient:
    def __init__(self, base_url, access_token):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    
    def query_knowledge_base(self, kb_id, query, method='hybrid_search', top_k=5):
        """查询知识库"""
        data = {
            'query': query,
            'method': method,
            'top_k': top_k,
            'use_rerank': True
        }
        response = requests.post(
            f'{self.base_url}/admin/knowledge-bases/{kb_id}/query',
            headers=self.headers,
            json=data
        )
        return response.json()

# 使用示例
client = RAGClient('https://api.example.com/api/v1', 'your-token')
result = client.query_knowledge_base(1, '如何配置系统？')
print(result['data']['results'])
```

## 注意事项

1. 所有请求都需要在请求头中包含有效的认证令牌：`Authorization: Bearer <token>`
2. 知识库训练是一个异步过程，可能需要一段时间才能完成
3. 查询知识库时，可以选择不同的检索方法：
   - `semantic_search`：语义搜索
   - `keyword_search`：关键词搜索
   - `hybrid_search`：混合搜索（默认）
4. 重排序模式包括：
   - `weighted_score`：加权分数（默认）
   - `cross_encoder`：交叉编码器重排序
   - `bm25`：BM25重排序
5. 支持的文档格式：PDF、Word、Excel、Markdown、HTML、TXT
6. 单个文件大小限制：50MB
7. 建议启用缓存以提高查询性能