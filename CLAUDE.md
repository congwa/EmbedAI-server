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