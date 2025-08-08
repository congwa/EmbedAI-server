# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Technology Stack

- **Backend**: FastAPI (Python 3.10+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis
- **Queue**: Huey (for async tasks like knowledge base training)
- **RAG Engine**: app/rag modules (for AI knowledge processing)
- **Deployment**: Docker (Dockerfile provided)
- **Package Manager**: Poetry

## Architecture Overview

This is the EmbedAI Server - a knowledge assistant system using RAG (Retrieval-Augmented Generation) technology and LLMs for high-performance semantic retrieval and intelligent Q&A services.

### RAG System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          EmbedAI RAG System                        │
├─────────────────────────────────────────────────────────────────────┤
│  FastAPI Server                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │   Auth & API    │  │   WebSocket     │  │   Admin Panel   │     │
│  │   Endpoints     │  │   Chat Server   │  │   Management    │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
├─────────────────────────────────────────────────────────────────────┤
│  RAG Processing Layer (app/rag/)                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │   Document      │  │   Embedding     │  │   Retrieval     │     │
│  │   Processing    │  │   Engine        │  │   Service       │     │
│  │                 │  │                 │  │                 │     │
│  │ • Extractor     │  │ • Vectorization │  │ • Semantic      │     │
│  │ • Splitter      │  │ • Caching       │  │   Search        │     │
│  │ • Cleaner       │  │ • Batch Proc.   │  │ • Reranking     │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
├─────────────────────────────────────────────────────────────────────┤
│  Data & Cache Layer                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │   PostgreSQL    │  │     Redis       │  │   Huey Queue    │     │
│  │                 │  │                 │  │                 │     │
│  │ • Metadata      │  │ • Query Cache   │  │ • Training      │     │
│  │ • Documents     │  │ • Vector Cache  │  │   Tasks         │     │
│  │ • Users         │  │ • Sessions      │  │ • Async Jobs    │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
├─────────────────────────────────────────────────────────────────────┤
│  External Services                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │   LLM Services  │  │   Embedding     │  │   Vector Store  │     │
│  │                 │  │   Services      │  │   (Optional)    │     │
│  │ • OpenAI        │  │ • OpenAI        │  │ • Milvus        │     │
│  │ • SiliconFlow   │  │ • SiliconFlow   │  │ • Pinecone      │     │
│  │ • Zhipu         │  │ • Local Models  │  │ • Chroma        │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
```

### RAG Data Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Document      │    │   Text          │    │   Vector        │
│   Upload        │───→│   Processing    │───→│   Generation    │
│                 │    │                 │    │                 │
│ • PDF, Word     │    │ • Extract       │    │ • Embed         │
│ • Excel, HTML   │    │ • Split         │    │ • Cache         │
│ • Text, MD      │    │ • Clean         │    │ • Index         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LLM           │    │   Context       │    │   Semantic      │
│   Response      │←───│   Assembly      │←───│   Retrieval     │
│                 │    │                 │    │                 │
│ • Generate      │    │ • Rerank        │    │ • Query Vector  │
│ • Stream        │    │ • Context       │    │ • Similarity    │
│ • Format        │    │ • Prompt        │    │ • Top-K         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       ▲
                                               ┌─────────────────┐
                                               │   User Query    │
                                               │   Processing    │
                                               │                 │
                                               │ • Vectorize     │
                                               │ • Normalize     │
                                               │ • Cache         │
                                               └─────────────────┘
```

### Core RAG Components

1. **Document Processing Pipeline**
   - Multi-format extraction (PDF, Word, Excel, HTML, etc.)
   - Intelligent text chunking with semantic awareness
   - Batch embedding generation with caching

2. **Semantic Retrieval Engine**
   - Vector similarity search
   - Hybrid search combining semantic and keyword matching
   - Advanced reranking algorithms

3. **LLM Integration**
   - Multiple LLM provider support (OpenAI, SiliconFlow, Zhipu)
   - Context-aware response generation
   - Token usage tracking and cost optimization

### Core Components Structure
- `/app/` - Main FastAPI application
  - `/api/v1/` - REST API endpoints
  - `/models/` - SQLAlchemy database models
  - `/services/` - Business logic services
  - `/core/` - Core configurations and middleware
  - `/schemas/` - Pydantic models for request/response
- `/app/rag/` - RAG (Retrieval-Augmented Generation) system
  - `/retrieval/` - Semantic retrieval services and engines
  - `/extractor/` - Document parsing and extraction utilities
  - `/embedding/` - Text embedding and vectorization services
  - `/splitter/` - Document chunking and splitting
  - `/rerank/` - Result reranking and optimization
  - `/training/` - Knowledge base training management

### Key Features

- Multi-tenant knowledge base isolation
- RAG-based knowledge processing and retrieval
- Semantic search with vector similarity matching
- Intelligent document chunking and embedding
- Real-time WebSocket chat support
- Multi-format document processing pipeline (PDF, Word, Excel, etc)
- Advanced reranking for improved result quality
- User authentication and authorization

## Development Commands

### Setup & Installation
```bash
# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Database Setup
```bash
# Create tables (automatic on startup)
alembic upgrade head

# Run migrations
alembic revision --autogenerate -m "description"
```

### Server Commands
```bash
# Development server with auto-reload
poetry run python main.py

# Production server
poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Docker deployment
docker build -t embedai-server .
docker run -p 8000:8000 embedai-server
```

### Testing
```bash
# Run all tests
poetry run pytest

# Run specific test file
poetry run pytest tests/test_auth.py

# Run with coverage
poetry run pytest --cov=app tests/
```

### Linting & Code Quality
```bash
# Type checking
poetry run mypy app/

# Code linting
poetry run flake8 app/

# Security scanning
poetry run bandit -r app/
```

## Configuration

- Environment variables in `.env` file (see `.env.example` if exists)
- Configuration handled in `app/core/config.py`
- Database connection via `DATABASE_URL`
- Redis connection via `REDIS_URL`
- LLM services via `SILICONFLOW_API_KEY`, `OPENAI_API_KEY`, etc.

## API Structure

- Base URL: `/api/v1`
- Authentication: JWT tokens (`Authorization: Bearer <token>`)
- WebSocket: `/ws/chat/{knowledge_base_id}` for real-time chat
- API documentation: Available at `/docs` when running locally

### Key API Endpoints

**Knowledge Base Management**
- `POST /api/v1/knowledge-bases` - Create knowledge base
- `GET /api/v1/knowledge-bases` - List knowledge bases
- `POST /api/v1/knowledge-bases/{id}/documents` - Upload documents
- `POST /api/v1/knowledge-bases/{id}/train` - Start RAG training

**RAG Search & Chat**
- `POST /api/v1/knowledge-bases/{id}/search` - Semantic search
- `POST /api/v1/chat/completions` - RAG-enhanced chat
- `GET /api/v1/knowledge-bases/{id}/status` - Training status

**Configuration**
- `GET /api/v1/knowledge-bases/{id}/config` - Get RAG configuration
- `PUT /api/v1/knowledge-bases/{id}/config` - Update RAG settings

## Database Models

- **User**: System users with authentication
- **KnowledgeBase**: Isolated knowledge containers with RAG configuration
- **Document**: Processed documents within knowledge bases
- **DocumentChunk**: Text chunks with embeddings for semantic search
- **ChatSession**: Chat interaction history

## RAG Knowledge Processing Pipeline

1. Document upload → extraction → intelligent splitting → embedding
2. Training queue management via Huey workers
3. Vector-based knowledge storage with semantic indexing
4. Real-time query processing with semantic retrieval and reranking

## Development Patterns & Conventions

### Service Layer Architecture
All business logic is encapsulated in service classes located in `/app/services/`. These services follow a pattern:
- **Base Service**: `app/services/base.py` provides CRUD operations
- **Entity Services**: Each model has a dedicated service (UserService, KnowledgeBaseService, etc.)
- **Composition**: Services can compose other services via dependency injection

### API Route Organization
```
api/v1/
├── admin/          # Admin-only endpoints (requires admin role)
├── client/         # Client endpoints (regular user access)
├── chat/           # WebSocket and chat functionality
└── ws/             # Real-time WebSocket handlers
```

### Asynchronous Patterns
- **Async/Await**: All I/O operations use async/await
- **Huey Tasks**: Long-running operations are offloaded to Huey workers
- **Database Sessions**: Scoped using FastAPI dependency injection in `app/core/database.py`
- **Redis**: Used for caching and session management via `app/core/redis_manager.py`

### Vector Database Integration Patterns
The RAG engine supports multiple vector databases through a factory pattern:
```
app/rag/datasource/vdb/
├── vector_factory.py    # Creates vector store instances
├── vector_base.py       # Abstract base class
├── vector_type.py       # Enum for supported vector stores
└── [provider]/          # Implementation for each vector database
```

### Caching Strategy
- **Redis Cache**: Query results and embeddings are cached in Redis
- **Cache Keys**: Follow pattern `{service}:{entity}:{id}:{operation}:{hash}`
- **TTL Values**: Configurable via environment variables (CACHE_TTL, EMBEDDING_CACHE_TTL)
- **Cache Invalidation**: Automatic on entity updates via service layer hooks

### Error Handling Patterns
- **Centralized Exceptions**: `app/core/exceptions.py` defines custom exceptions
- **Global Exception Handler**: FastAPI exception handlers in `app/main.py`
- **Error Responses**: Standardized JSON responses following OpenAPI schema
- **Logging**: Structured logging with `app/core/logger.py` using different log levels

### Configuration Management
- **Environment Vars**: Load from `.env` via `app/core/config.py`
- **Pydantic Settings**: Runtime configuration validation
- **Dynamic Configuration**: Certain settings update without restart
- **Override Hierarchy**: Env vars > config file > defaults

### Testing Conventions
- **Test Structure**: Organized by test type (`tests/unit/`, `tests/integration/`, `tests/e2e/`)
- **Fixtures**: Common test data in `tests/conftest.py`
- **Mocking**: External services (LLM APIs, vector stores) are mocked
- **Integration Tests**: Use `httpx.AsyncClient` for API testing
- **Performance Tests**: `tests/performance/locustfile.py` for load testing

### Database Migrations
- **Alembic**: All schema changes via alembic migrations
- **Auto-generation**: Use `alembic revision --autogenerate -m "description"`
- **Data Migrations**: Include both schema and data migrations
- **Production**: Always run `alembic upgrade head` before starting service

### Code Quality & Standards
- **Type Hints**: All functions and methods use type annotations (mypy compliant)
- **Docstrings**: Google-style docstrings for all public methods
- **Black Format**: Consistent code formatting (line length 88)
- **Flake8**: Linting rules defined in `pyproject.toml`
- **Security**: Bandit static analysis for common security issues

## Common Development Commands

### Quick Start Commands
```bash
# Install environment
python -m pip install poetry
poetry install
poetry shell

# Run with auto-reload (dev)
poetry run python -m main

# Run with uvicorn (dev)
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests
poetry run pytest tests/unit/test_user_service.py -v
poetry run pytest tests/integration/test_admin_apis.py -v
poetry run pytest --cov=app --cov-report=html
```

### Debugging Tools
```bash
# Interactive development
python -m IPython -i
from app.core.database import get_db
from app.services.knowledge_base import KnowledgeBaseService

# Debug RAG pipeline
from app.rag.retrieval.retrieval_service import RetrievalService
from app.rag.embedding.embedding_engine import EmbeddingEngine

# Validate service health
curl http://localhost:8000/health
```

### Working with Vector Stores
```python
# Adding new vector store provider
from app.rag.datasource.vdb.vector_base import VectorBase
class CustomVectorStore(VectorBase):
    # Implement required abstract methods
    pass

# Register in vector_factory.py
from app.rag.datasource.vdb.vector_type import VectorType
VECTOR_MAP[VectorType.CUSTOM] = CustomVectorStore
```

### Testing RAG Components
```python
# Test embedding
from app.rag.embedding.embedding_engine import EmbeddingEngine
engine = EmbeddingEngine(llm_config)
vector = await engine.embed_query("test query")

# Test retrieval
results = await retrieval.query("test query", method="semantic_search")
print(f"Found {len(results)} relevant chunks")
```

## Environment Configuration Reference

### Required Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/embedai

# Redis
REDIS_URL=redis://localhost:6379/0

# LLM Services (at least one required)
SILICONFLOW_API_KEY=sk-your-key
OPENAI_API_KEY=sk-your-key
ZHIPU_API_KEY=your-zhipu-key
```

### Optional Configuration
```bash
# RAG Engine
DEFAULT_CHUNK_SIZE=1000
DEFAULT_CHUNK_OVERLAP=200
DEFAULT_TOP_K=5
EMBEDDING_MODEL=text-embedding-ada-002
VECTOR_STORE=pgvector  # or chroma, qdrant, etc.

# Performance
WORKERS=4
MAX_CONNECTIONS=100
CACHE_TTL=3600
BATCH_SIZE=100
```

### Development-Specific
```bash
DEBUG=true
LOG_LEVEL=DEBUG
TEST_MODE=true
MOCK_LLM_RESPONSES=true  # For testing without API calls
```

## API Design Patterns

### Response Structure
All API responses follow a standard format:
```json
{
  "data": {...},  // Success data or null
  "error": null,  // Error object or null
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z",
    "version": "v1"
  }
}
```

### Error Responses
```json
{
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {...}
  }
}
```

### Pagination
All list endpoints support pagination:
```json
{
  "data": {
    "items": [...],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 100,
      "total_pages": 5
    }
  }
}
```