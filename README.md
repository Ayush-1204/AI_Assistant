# Phase 0 – Project Foundation

## Vision
Build a modular, scalable, AI-first operating system that unifies chat, memory, notes, documents, calendar, tasks, voice, search, and autonomous agents into a single personalized platform.

## Architectural Principles

- Monorepo architecture for all applications and shared packages.
- Domain-Driven Design (DDD) with feature-based modules.
- Plugin-based architecture for future extensibility.
- Centralized LLM Gateway supporting multiple AI providers.
- Event-driven communication between services.
- Local-first deployment with optional cloud providers.
- Production-ready infrastructure from day one.

## Planned Technology Stack

### Frontend
- Flutter (Web, Android, iOS, Desktop)

### Backend
- FastAPI
- PostgreSQL
- Redis
- Qdrant
- MinIO
- Celery

### AI
- Ollama
- Whisper
- Piper
- Qwen / Llama / Mistral

### Infrastructure
- Docker
- Docker Compose
- Nginx
- GitHub Actions
- Prometheus
- Grafana

## Repository Layout

apps/
packages/
services/
infrastructure/
docs/
scripts/
.github/

This architecture is designed for long-term scalability, allowing new services such as Email, GitHub, Slack, and WhatsApp integrations to be added without major refactoring.

----------------------------------------------------------------------------------------------------

# Phase 1 – Backend Foundation

## Objective

Establish a production-ready backend foundation before implementing application features.

## Repository Principles

- Feature-based architecture (Domain-Driven Design)
- Async-first FastAPI backend
- Repository-Service pattern
- Centralized LLM Gateway
- Environment-based configuration
- Structured logging
- Dockerized local development
- Comprehensive testing from the start

## Backend Standards

- Python 3.12
- FastAPI
- PostgreSQL
- Redis
- Qdrant
- MinIO
- Ollama
- Docker Compose

## Module Structure

Each feature is organized into its own module containing:

- API layer
- Business service
- Repository
- Database models
- Schemas
- Events
- Dependencies
- Exceptions
- Constants
- Tests

This architecture promotes scalability, maintainability, and independent feature development while minimizing coupling between modules.

-----------------------------------------------------------

# Sprint 1 – Backend Bootstrap

## Objective

Initialize the FastAPI backend with a clean, production-ready structure.

## Implemented

- FastAPI application bootstrap
- Environment-based configuration using `pydantic-settings`
- Application lifespan management
- Centralized logging setup using `structlog`
- Health and root endpoints
- Router-based API organization
- Virtual environment and dependency setup

## Project Structure

```
app/
├── main.py
├── config.py
├── logging.py
├── lifespan.py
└── routers/
    └── health.py
```

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| GET | `/health` | Health check |

## Run

```bash
uvicorn app.main:app --reload
```

The backend now provides a minimal but extensible foundation that future services (authentication, memory, chat, RAG, agents, etc.) will build upon.

-----------------------------------------------------------

# Sprint 1 – Commit 2

## Objective

Prepare the FastAPI backend for future features without modifying the existing architecture.

## Changes

- Added project directories for `services`, `repositories`, `models`, `schemas`, and `utils`.
- Extended configuration to support database and JWT settings.
- Improved logging with structured JSON output using `structlog`.
- Updated environment template with placeholders for PostgreSQL and authentication.
- Kept the original project structure unchanged while making it ready for future modules.

## New Environment Variables

- `DATABASE_URL`
- `JWT_SECRET`
- `JWT_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`

## Result

The backend remains simple and functional while being prepared for database integration, authentication, and feature-based development in subsequent commits.

-----------------------------------------------------------

