# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Technology Stack
- **Backend**: FastAPI (Python 3.10+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis
- **Queue**: Huey (for async tasks like knowledge base training)
- **Graph Database**: Neo4j (for AI knowledge storage)
- **Deployment**: Docker (Dockerfile provided)
- **Package Manager**: Poetry

## Architecture Overview

This is the EmbedAI Server - a knowledge assistant system using graph databases and LLMs for high-performance knowledge retrieval and intelligent Q&A services.

### Core Components Structure
- `/app/` - Main FastAPI application
  - `/api/v1/` - REST API endpoints
  - `/models/` - SQLAlchemy database models
  - `/services/` - Business logic services
  - `/core/` - Core configurations and middleware
  - `/schemas/` - Pydantic models for request/response
- `/_rag/` - RAG (Retrieval-Augmented Generation) system
  - `/retrieval/` - Knowledge retrieval algorithms
  - `/extractor/` - Document parsing and extraction utilities
  - `/embedding/` - Text embedding services
  - `/rag/docstore/` - Document storage and retrieval

### Key Features
- Multi-tenant knowledge base isolation
- Graph-based knowledge storage (Neo4j)
- Intelligent entity recognition and relationship analysis
- Vector similarity search with multi-hop graph traversal
- Real-time WebSocket chat support
- Document processing pipeline (PDF, text, Excel, etc)
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
- Neo4j connection via `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`

## API Structure
- Base URL: `/api/v1`
- Authentication: JWT tokens (`Authorization: Bearer <token>`)
- WebSocket: `/ws/chat/{knowledge_base_id}` for real-time chat
- API documentation: Available at `/docs` when running locally

## Database Models
- **User**: System users with authentication
- **KnowledgeBase**: Isolated knowledge containers
- **Document**: Processed documents within knowledge bases
- **ChatSession**: Chat interaction history
- **Entity/Relation**: Graph nodes and edges for AI knowledge

## Knowledge Processing Pipeline
1. Document upload → extraction → splitting → embedding
2. Training queue management via Huey workers
3. Graph-based knowledge storage with Neo4j
4. Real-time query processing with vector + graph retrieval