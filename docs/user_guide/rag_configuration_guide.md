# RAG功能配置指南

## 概述

本指南详细介绍了RAG（Retrieval-Augmented Generation）功能的各种配置选项，帮助您根据具体需求优化系统性能。

## 系统配置

### 环境变量配置

在 `.env` 文件中添加以下配置：

```bash
# === RAG核心配置 ===
# 向量数据库类型 (chroma, qdrant)
VECTOR_DB_TYPE=chroma

# 文本分块配置
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=200
RAG_MAX_CHUNK_SIZE=4000

# 向量化配置
RAG_EMBEDDING_BATCH_SIZE=100
RAG_EMBEDDING_CACHE_TTL=604800  # 7天

# 检索配置
RAG_DEFAULT_TOP_K=10
RAG_SCORE_THRESHOLD=0.7
RAG_ENABLE_RERANK=true

# 性能配置
RAG_MAX_WORKERS=4
RAG_TIMEOUT=300
RAG_MAX_FILE_SIZE=52428800  # 50MB

# === Chroma配置 ===
CHROMA_PERSIST_DIRECTORY=./data/chroma_db
CHROMA_HOST=localhost
CHROMA_PORT=8000

# === Qdrant配置 ===
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=your-qdrant-api-key
QDRANT_HTTPS=false

# === Redis缓存配置 ===
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your-redis-password

# === OpenAI配置 ===
OPENAI_API_KEY=your-openai-api-key
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

# === 日志配置 ===
RAG_LOG_LEVEL=INFO
RAG_LOG_FILE=./logs/rag.log
RAG_LOG_MAX_SIZE=10485760  # 10MB
RAG_LOG_BACKUP_COUNT=5
```

### 应用配置

在 `app/core/config.py` 中的配置项：

```python
class Settings(BaseSettings):
    # RAG核心配置
    RAG_CHUNK_SIZE: int = 1000
    RAG_CHUNK_OVERLAP: int = 200
    RAG_MAX_CHUNK_SIZE: int = 4000
    RAG_EMBEDDING_BATCH_SIZE: int = 100
    RAG_EMBEDDING_CACHE_TTL: int = 604800
    RAG_DEFAULT_TOP_K: int = 10
    RAG_SCORE_THRESHOLD: float = 0.7
    RAG_ENABLE_RERANK: bool = True
    RAG_MAX_WORKERS: int = 4
    RAG_TIMEOUT: int = 300
    RAG_MAX_FILE_SIZE: int = 52428800
    
    # 向量数据库配置
    VECTOR_DB_TYPE: str = "chroma"
    CHROMA_PERSIST_DIRECTORY: str = "./data/chroma_db"
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000
    
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_HTTPS: bool = False
    
    # 支持的文档格式
    RAG_SUPPORTED_FORMATS: List[str] = [
        "pdf", "docx", "xlsx", "md", "html", "txt"
    ]
    
    # 文本分块策略
    RAG_SPLITTING_STRATEGIES: List[str] = [
        "recursive_character", "fixed", "semantic"
    ]
    
    # 检索方法
    RAG_RETRIEVAL_METHODS: List[str] = [
        "semantic_search", "keyword_search", "hybrid_search"
    ]
    
    # 重排序模式
    RAG_RERANK_MODES: List[str] = [
        "weighted_score", "cross_encoder", "bm25"
    ]
```

## 文档处理配置

### 支持的文档格式配置

```python
# 文档格式处理器配置
DOCUMENT_PROCESSORS = {
    "pdf": {
        "class": "PDFExtractor",
        "options": {
            "extract_images": False,
            "extract_tables": True,
            "ocr_enabled": False
        }
    },
    "docx": {
        "class": "WordExtractor",
        "options": {
            "extract_images": False,
            "extract_tables": True,
            "preserve_formatting": True
        }
    },
    "xlsx": {
        "class": "ExcelExtractor",
        "options": {
            "extract_all_sheets": True,
            "include_formulas": False
        }
    },
    "md": {
        "class": "MarkdownExtractor",
        "options": {
            "preserve_code_blocks": True,
            "extract_links": True
        }
    },
    "html": {
        "class": "HTMLExtractor",
        "options": {
            "extract_text_only": True,
            "preserve_links": True,
            "remove_scripts": True
        }
    },
    "txt": {
        "class": "TextExtractor",
        "options": {
            "encoding": "utf-8",
            "detect_encoding": True
        }
    }
}
```

### 文本清理配置

```python
# 文本清理选项
TEXT_CLEANING_OPTIONS = {
    "remove_extra_whitespace": True,
    "normalize_unicode": True,
    "remove_control_characters": True,
    "fix_encoding_errors": True,
    "remove_empty_lines": True,
    "trim_lines": True,
    "min_line_length": 3,
    "max_line_length": 10000
}
```

## 文本分块配置

### 递归字符分块配置

```python
RECURSIVE_CHARACTER_SPLITTER_CONFIG = {
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "separators": ["\n\n", "\n", " ", ""],
    "keep_separator": True,
    "is_separator_regex": False,
    "length_function": len
}
```

### 固定长度分块配置

```python
FIXED_TEXT_SPLITTER_CONFIG = {
    "chunk_size": 500,
    "chunk_overlap": 50,
    "separator": " ",
    "keep_separator": False
}
```

### 语义分块配置

```python
SEMANTIC_SPLITTER_CONFIG = {
    "buffer_size": 1,
    "breakpoint_threshold_type": "percentile",
    "breakpoint_threshold_amount": 95,
    "number_of_chunks": None
}
```

## 向量化配置

### OpenAI Embedding配置

```python
OPENAI_EMBEDDING_CONFIG = {
    "provider": "openai",
    "model": "text-embedding-ada-002",
    "api_key": "your-api-key",
    "api_base": "https://api.openai.com/v1",
    "batch_size": 100,
    "max_retries": 3,
    "timeout": 60,
    "dimensions": 1536
}
```

### HuggingFace Embedding配置

```python
HUGGINGFACE_EMBEDDING_CONFIG = {
    "provider": "huggingface",
    "model": "sentence-transformers/all-MiniLM-L6-v2",
    "device": "cpu",  # 或 "cuda"
    "batch_size": 50,
    "normalize_embeddings": True,
    "cache_folder": "./models/huggingface"
}
```

### 本地模型配置

```python
LOCAL_EMBEDDING_CONFIG = {
    "provider": "local",
    "model_path": "./models/embedding_model",
    "device": "cpu",
    "batch_size": 32,
    "max_seq_length": 512
}
```

## 向量存储配置

### Chroma配置

```python
CHROMA_CONFIG = {
    "type": "chroma",
    "persist_directory": "./data/chroma_db",
    "host": "localhost",
    "port": 8000,
    "ssl": False,
    "headers": {},
    "collection_metadata": {
        "hnsw:space": "cosine",
        "hnsw:construction_ef": 100,
        "hnsw:M": 16
    },
    "embedding_function": None  # 使用默认
}
```

### Qdrant配置

```python
QDRANT_CONFIG = {
    "type": "qdrant",
    "host": "localhost",
    "port": 6333,
    "grpc_port": 6334,
    "prefer_grpc": False,
    "https": False,
    "api_key": None,
    "prefix": None,
    "timeout": 20,
    "collection_config": {
        "vectors": {
            "size": 1536,
            "distance": "Cosine"
        },
        "optimizers_config": {
            "default_segment_number": 2,
            "max_segment_size": 20000,
            "memmap_threshold": 50000,
            "indexing_threshold": 20000,
            "flush_interval_sec": 5,
            "max_optimization_threads": 1
        },
        "replication_factor": 1,
        "write_consistency_factor": 1
    }
}
```

## 检索配置

### 语义搜索配置

```python
SEMANTIC_SEARCH_CONFIG = {
    "method": "semantic_search",
    "top_k": 10,
    "score_threshold": 0.7,
    "filter": None,
    "search_params": {
        "ef": 128,  # for HNSW
        "nprobe": 10  # for IVF
    }
}
```

### 关键词搜索配置

```python
KEYWORD_SEARCH_CONFIG = {
    "method": "keyword_search",
    "top_k": 10,
    "analyzer": "standard",
    "use_stemming": True,
    "use_synonyms": False,
    "boost_fields": {
        "title": 2.0,
        "content": 1.0
    },
    "minimum_should_match": "75%"
}
```

### 混合搜索配置

```python
HYBRID_SEARCH_CONFIG = {
    "method": "hybrid_search",
    "top_k": 10,
    "semantic_weight": 0.7,
    "keyword_weight": 0.3,
    "normalization": "min_max",
    "fusion_method": "rrf"  # reciprocal rank fusion
}
```

## 重排序配置

### 权重重排序配置

```python
WEIGHTED_RERANK_CONFIG = {
    "mode": "weighted_score",
    "weights": {
        "semantic_score": 0.6,
        "keyword_score": 0.3,
        "recency_score": 0.1
    },
    "normalization": "softmax"
}
```

### 交叉编码器重排序配置

```python
CROSS_ENCODER_RERANK_CONFIG = {
    "mode": "cross_encoder",
    "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
    "batch_size": 32,
    "max_length": 512,
    "device": "cpu"
}
```

### BM25重排序配置

```python
BM25_RERANK_CONFIG = {
    "mode": "bm25",
    "k1": 1.2,
    "b": 0.75,
    "epsilon": 0.25,
    "use_idf": True
}
```

## 缓存配置

### Redis缓存配置

```python
REDIS_CACHE_CONFIG = {
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "password": None,
    "socket_timeout": 5,
    "socket_connect_timeout": 5,
    "socket_keepalive": True,
    "socket_keepalive_options": {},
    "connection_pool_kwargs": {
        "max_connections": 50
    },
    "decode_responses": True,
    "encoding": "utf-8"
}
```

### 缓存策略配置

```python
CACHE_STRATEGY_CONFIG = {
    "query_cache": {
        "enabled": True,
        "ttl": 3600,  # 1小时
        "max_size": 1000,
        "key_prefix": "rag:query:"
    },
    "embedding_cache": {
        "enabled": True,
        "ttl": 604800,  # 7天
        "max_size": 10000,
        "key_prefix": "rag:embedding:"
    },
    "index_cache": {
        "enabled": True,
        "ttl": 86400,  # 1天
        "max_size": 100,
        "key_prefix": "rag:index:"
    }
}
```

## 性能配置

### 并发配置

```python
CONCURRENCY_CONFIG = {
    "max_workers": 4,
    "thread_pool_size": 10,
    "process_pool_size": 2,
    "async_timeout": 300,
    "batch_processing": {
        "document_batch_size": 10,
        "embedding_batch_size": 100,
        "index_batch_size": 1000
    }
}
```

### 内存配置

```python
MEMORY_CONFIG = {
    "max_memory_usage": "2GB",
    "embedding_cache_size": "500MB",
    "document_cache_size": "200MB",
    "gc_threshold": 0.8,
    "memory_check_interval": 60
}
```

## 日志配置

### 日志级别配置

```python
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
        "detailed": {
            "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s"
        }
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "standard"
        },
        "file": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "./logs/rag.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "detailed"
        }
    },
    "loggers": {
        "app.rag": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
            "propagate": False
        }
    }
}
```

## 安全配置

### API安全配置

```python
SECURITY_CONFIG = {
    "api_rate_limit": {
        "requests_per_minute": 100,
        "requests_per_hour": 1000
    },
    "file_upload": {
        "max_file_size": 52428800,  # 50MB
        "allowed_extensions": [".pdf", ".docx", ".xlsx", ".md", ".html", ".txt"],
        "scan_for_malware": True
    },
    "data_privacy": {
        "encrypt_embeddings": False,
        "anonymize_logs": True,
        "data_retention_days": 365
    }
}
```

## 监控配置

### 性能监控配置

```python
MONITORING_CONFIG = {
    "metrics": {
        "enabled": True,
        "export_interval": 60,
        "metrics_port": 9090
    },
    "health_check": {
        "enabled": True,
        "check_interval": 30,
        "timeout": 10
    },
    "alerts": {
        "enabled": True,
        "email_notifications": True,
        "webhook_url": None,
        "thresholds": {
            "response_time": 5000,  # 5秒
            "error_rate": 0.05,     # 5%
            "memory_usage": 0.8     # 80%
        }
    }
}
```

## 配置验证

### 配置验证脚本

```python
# scripts/validate_config.py
import os
from app.core.config import Settings

def validate_rag_config():
    """验证RAG配置"""
    settings = Settings()
    
    # 验证必需的配置
    required_configs = [
        "VECTOR_DB_TYPE",
        "RAG_CHUNK_SIZE",
        "RAG_EMBEDDING_BATCH_SIZE"
    ]
    
    for config in required_configs:
        if not hasattr(settings, config):
            raise ValueError(f"缺少必需的配置: {config}")
    
    # 验证向量数据库配置
    if settings.VECTOR_DB_TYPE == "chroma":
        if not settings.CHROMA_PERSIST_DIRECTORY:
            raise ValueError("Chroma配置缺少persist_directory")
    elif settings.VECTOR_DB_TYPE == "qdrant":
        if not settings.QDRANT_HOST:
            raise ValueError("Qdrant配置缺少host")
    
    # 验证文件大小限制
    if settings.RAG_MAX_FILE_SIZE > 104857600:  # 100MB
        print("警告: 文件大小限制过大，可能影响性能")
    
    print("配置验证通过")

if __name__ == "__main__":
    validate_rag_config()
```

## 配置模板

### 开发环境配置模板

```bash
# .env.development
VECTOR_DB_TYPE=chroma
CHROMA_PERSIST_DIRECTORY=./data/dev/chroma_db
RAG_CHUNK_SIZE=500
RAG_EMBEDDING_BATCH_SIZE=50
RAG_LOG_LEVEL=DEBUG
RAG_ENABLE_RERANK=false
```

### 生产环境配置模板

```bash
# .env.production
VECTOR_DB_TYPE=qdrant
QDRANT_HOST=qdrant.example.com
QDRANT_PORT=6333
QDRANT_API_KEY=your-production-api-key
RAG_CHUNK_SIZE=1000
RAG_EMBEDDING_BATCH_SIZE=100
RAG_LOG_LEVEL=INFO
RAG_ENABLE_RERANK=true
RAG_MAX_WORKERS=8
```

### 测试环境配置模板

```bash
# .env.test
VECTOR_DB_TYPE=chroma
CHROMA_PERSIST_DIRECTORY=./data/test/chroma_db
RAG_CHUNK_SIZE=200
RAG_EMBEDDING_BATCH_SIZE=10
RAG_LOG_LEVEL=WARNING
RAG_TIMEOUT=60
```

## 配置最佳实践

### 1. 性能优化配置

- **文档处理**: 根据文档类型调整chunk_size
- **向量化**: 使用合适的batch_size平衡速度和内存
- **缓存**: 启用缓存以提高重复查询性能
- **并发**: 根据硬件配置调整max_workers

### 2. 内存管理配置

- **监控内存使用**: 设置合理的内存限制
- **垃圾回收**: 配置适当的GC阈值
- **缓存大小**: 根据可用内存设置缓存大小

### 3. 安全配置

- **API限制**: 设置合理的请求频率限制
- **文件验证**: 启用文件类型和大小验证
- **数据加密**: 在生产环境中启用数据加密

### 4. 监控配置

- **日志级别**: 生产环境使用INFO，开发环境使用DEBUG
- **性能指标**: 启用性能监控和告警
- **健康检查**: 配置定期健康检查

---

*本配置指南涵盖了RAG功能的所有主要配置选项，请根据您的具体需求进行调整。*