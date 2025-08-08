# 配置管理API文档

本文档描述了配置管理系统的API接口，包括提示词管理配置和RAG配置的管理功能。

## 概述

配置管理API提供了对系统核心配置的管理功能，支持：
- 提示词管理配置的查看、更新、验证和重置
- RAG配置的查看、更新、验证和重置
- 配置选项和统计信息的获取
- 配置变更历史的查询

## 基础信息

- **基础URL**: `/api/v1/admin/config`
- **认证方式**: Bearer Token（需要管理员权限）
- **响应格式**: JSON

## 提示词管理配置接口

### 1. 获取提示词配置

获取当前的提示词管理配置。

```http
GET /api/v1/admin/config/prompt
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "max_length": 50000,
    "max_variables": 50,
    "version_limit": 100,
    "cache_ttl": 3600,
    "default_category": "通用",
    "enable_analytics": true,
    "retention_days": 90,
    "suggestions_limit": 10,
    "batch_size": 100,
    "enable_auto_optimization": false,
    "last_updated": "2024-01-15T10:30:00",
    "cache_status": "active"
  }
}
```

### 2. 更新提示词配置

更新提示词管理配置的部分或全部设置。

```http
PUT /api/v1/admin/config/prompt
```

**请求体**:
```json
{
  "max_length": 60000,
  "max_variables": 60,
  "enable_analytics": true,
  "retention_days": 120
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "max_length": 60000,
    "max_variables": 60,
    "version_limit": 100,
    "cache_ttl": 3600,
    "default_category": "通用",
    "enable_analytics": true,
    "retention_days": 120,
    "suggestions_limit": 10,
    "batch_size": 100,
    "enable_auto_optimization": false
  }
}
```

### 3. 重置提示词配置

将提示词配置重置为默认值。

```http
POST /api/v1/admin/config/prompt/reset
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "max_length": 50000,
    "max_variables": 50,
    "version_limit": 100,
    "cache_ttl": 3600,
    "default_category": "通用",
    "enable_analytics": true,
    "retention_days": 90,
    "suggestions_limit": 10,
    "batch_size": 100,
    "enable_auto_optimization": false
  }
}
```

### 4. 验证提示词配置

验证提示词配置数据的有效性。

```http
POST /api/v1/admin/config/prompt/validate
```

**请求体**:
```json
{
  "max_length": 50000,
  "max_variables": 50,
  "version_limit": 100,
  "cache_ttl": 3600,
  "enable_analytics": true
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "valid": true,
    "validated_config": {
      "max_length": 50000,
      "max_variables": 50,
      "version_limit": 100,
      "cache_ttl": 3600,
      "enable_analytics": true
    },
    "errors": [],
    "warnings": []
  }
}
```

### 5. 获取提示词配置选项

获取提示词配置的所有可用选项和限制。

```http
GET /api/v1/admin/config/prompt/options
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "max_length": {
      "min": 100,
      "max": 100000,
      "default": 50000,
      "description": "提示词模板最大长度（字符）"
    },
    "max_variables": {
      "min": 1,
      "max": 100,
      "default": 50,
      "description": "模板最大变量数量"
    },
    "version_limit": {
      "min": 10,
      "max": 1000,
      "default": 100,
      "description": "版本历史保留数量"
    },
    "cache_ttl": {
      "min": 60,
      "max": 86400,
      "default": 3600,
      "description": "缓存过期时间（秒）"
    },
    "retention_days": {
      "min": 7,
      "max": 365,
      "default": 90,
      "description": "使用统计数据保留天数"
    },
    "enable_analytics": {
      "type": "boolean",
      "default": true,
      "description": "是否启用使用统计"
    },
    "enable_auto_optimization": {
      "type": "boolean",
      "default": false,
      "description": "是否启用自动优化建议"
    }
  }
}
```

### 6. 获取提示词配置统计

获取与提示词配置相关的统计信息。

```http
GET /api/v1/admin/config/prompt/stats
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "total_templates": 25,
    "total_usage": 1250,
    "today_usage": 45,
    "config_last_updated": "2024-01-15T10:30:00",
    "cache_status": "active"
  }
}
```

### 7. 获取提示词配置变更历史

获取提示词配置的变更历史记录。

```http
GET /api/v1/admin/config/prompt/history?limit=10
```

**查询参数**:
- `limit` (可选): 返回记录数量，默认10，最大100

**响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "timestamp": "2024-01-15T10:30:00",
      "user_id": 1,
      "action": "update",
      "changes": {
        "max_length": {
          "old": 50000,
          "new": 60000
        }
      },
      "version": "1.0.0"
    }
  ]
}
```

## RAG配置接口

### 1. 获取RAG配置

获取当前的RAG配置。

```http
GET /api/v1/admin/config/rag
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "vector_store_type": "chroma",
    "batch_size": 100,
    "rerank_model": "bge-reranker-base",
    "retrieval_method": "hybrid_search",
    "use_rerank": true,
    "last_updated": "2024-01-15T10:30:00",
    "cache_status": "active"
  }
}
```

### 2. 更新RAG配置

更新RAG配置的部分或全部设置。

```http
PUT /api/v1/admin/config/rag
```

**请求体**:
```json
{
  "chunk_size": 1200,
  "chunk_overlap": 250,
  "use_rerank": true,
  "retrieval_method": "hybrid_search"
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "chunk_size": 1200,
    "chunk_overlap": 250,
    "vector_store_type": "chroma",
    "batch_size": 100,
    "rerank_model": "bge-reranker-base",
    "retrieval_method": "hybrid_search",
    "use_rerank": true
  }
}
```

### 3. 重置RAG配置

将RAG配置重置为默认值。

```http
POST /api/v1/admin/config/rag/reset
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "vector_store_type": "chroma",
    "batch_size": 100,
    "rerank_model": "bge-reranker-base",
    "retrieval_method": "hybrid_search",
    "use_rerank": true
  }
}
```

### 4. 验证RAG配置

验证RAG配置数据的有效性。

```http
POST /api/v1/admin/config/rag/validate
```

**请求体**:
```json
{
  "chunk_size": 1000,
  "chunk_overlap": 200,
  "vector_store_type": "chroma",
  "use_rerank": true
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "valid": true,
    "validated_config": {
      "chunk_size": 1000,
      "chunk_overlap": 200,
      "vector_store_type": "chroma",
      "use_rerank": true
    },
    "errors": [],
    "warnings": []
  }
}
```

### 5. 获取RAG配置选项

获取RAG配置的所有可用选项和限制。

```http
GET /api/v1/admin/config/rag/options
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "chunk_size": {
      "min": 100,
      "max": 10000,
      "default": 1000,
      "description": "文本分块大小（字符）"
    },
    "chunk_overlap": {
      "min": 0,
      "max": 5000,
      "default": 200,
      "description": "文本分块重叠大小（字符）"
    },
    "vector_store_type": {
      "type": "enum",
      "options": ["chroma", "qdrant", "milvus", "pgvector"],
      "default": "chroma",
      "description": "向量存储类型"
    },
    "retrieval_method": {
      "type": "enum",
      "options": ["semantic_search", "keyword_search", "hybrid_search"],
      "default": "hybrid_search",
      "description": "检索方法"
    },
    "use_rerank": {
      "type": "boolean",
      "default": true,
      "description": "是否使用重排序"
    }
  }
}
```

### 6. 获取RAG配置统计

获取与RAG配置相关的统计信息。

```http
GET /api/v1/admin/config/rag/stats
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "total_knowledge_bases": 15,
    "total_documents": 450,
    "today_knowledge_bases": 2,
    "config_last_updated": "2024-01-15T10:30:00",
    "cache_status": "active"
  }
}
```

## 配置参数说明

### 提示词配置参数

| 参数名 | 类型 | 默认值 | 范围 | 说明 |
|--------|------|--------|------|------|
| max_length | int | 50000 | 100-100000 | 提示词模板最大长度（字符） |
| max_variables | int | 50 | 1-100 | 模板最大变量数量 |
| version_limit | int | 100 | 10-1000 | 版本历史保留数量 |
| cache_ttl | int | 3600 | 60-86400 | 缓存过期时间（秒） |
| default_category | str | "通用" | - | 默认分类名称 |
| enable_analytics | bool | true | - | 是否启用使用统计 |
| retention_days | int | 90 | 7-365 | 统计数据保留天数 |
| suggestions_limit | int | 10 | 1-50 | 模板建议数量限制 |
| batch_size | int | 100 | 1-1000 | 批处理大小 |
| enable_auto_optimization | bool | false | - | 是否启用自动优化建议 |

### RAG配置参数

| 参数名 | 类型 | 默认值 | 范围/选项 | 说明 |
|--------|------|--------|-----------|------|
| chunk_size | int | 1000 | 100-10000 | 文本分块大小（字符） |
| chunk_overlap | int | 200 | 0-5000 | 文本分块重叠大小（字符） |
| vector_store_type | str | "chroma" | chroma, qdrant, milvus, pgvector | 向量存储类型 |
| batch_size | int | 100 | 1-1000 | 批处理大小 |
| rerank_model | str | "bge-reranker-base" | - | 重排序模型名称 |
| retrieval_method | str | "hybrid_search" | semantic_search, keyword_search, hybrid_search | 检索方法 |
| use_rerank | bool | true | - | 是否使用重排序 |

## 错误处理

所有接口都遵循统一的错误响应格式：

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "配置验证失败",
    "details": "max_length 必须是100-100000之间的整数"
  }
}
```

常见错误码：
- `VALIDATION_ERROR`: 配置验证失败
- `PERMISSION_DENIED`: 权限不足
- `CONFIG_NOT_FOUND`: 配置不存在
- `INTERNAL_ERROR`: 内部服务器错误

## 使用示例

### Python示例

```python
import requests

# 获取提示词配置
response = requests.get(
    "http://localhost:8000/api/v1/admin/config/prompt",
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
config = response.json()["data"]

# 更新配置
update_data = {
    "max_length": 60000,
    "enable_analytics": True
}
response = requests.put(
    "http://localhost:8000/api/v1/admin/config/prompt",
    json=update_data,
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
```

### JavaScript示例

```javascript
// 获取RAG配置
const response = await fetch('/api/v1/admin/config/rag', {
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN',
    'Content-Type': 'application/json'
  }
});
const config = await response.json();

// 更新配置
const updateData = {
  chunk_size: 1200,
  use_rerank: true
};
const updateResponse = await fetch('/api/v1/admin/config/rag', {
  method: 'PUT',
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(updateData)
});
```

## 注意事项

1. **权限要求**: 所有配置管理接口都需要管理员权限
2. **配置验证**: 更新配置时会自动进行验证，无效的配置会被拒绝
3. **缓存机制**: 配置更新后会自动更新缓存
4. **变更记录**: 所有配置变更都会被记录到日志中
5. **默认值**: 重置配置会恢复到系统默认值
6. **批量更新**: 支持部分配置更新，未指定的配置项保持不变

## 版本历史

- v1.0.0: 初始版本，支持基础的配置管理功能
- v1.1.0: 添加配置选项和统计信息接口
- v1.2.0: 添加配置验证和历史记录功能