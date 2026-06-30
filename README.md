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

# Sprint 2 – Database Foundation

## Objective

Establish the database layer that all persistent application features will use.

## Added Components

- SQLAlchemy ORM
- PostgreSQL configuration
- Declarative base class
- Database session factory

## Directory Structure

```text
app/
├── db/
│   ├── base.py
│   ├── session.py
│   └── models/
```

## Responsibilities

- `base.py` defines the base class for all database models.
- `session.py` creates the SQLAlchemy engine and session factory.
- Database configuration is loaded from environment variables.

## Current Status

The application now has the foundation required for persistent storage. Database models and migrations will be introduced in the following sprint.

-------------------------------------------------------------------

PostGRE setup done.

# Environment Configuration

## Purpose

The application loads runtime configuration from a local `.env` file.

### Files

- `.env.example` — Template committed to Git.
- `.env` — Local configuration file containing environment-specific values and secrets. This file is excluded from version control.

## Database Configuration

The `DATABASE_URL` environment variable defines the PostgreSQL connection string used by SQLAlchemy's asynchronous engine.

-------------------------------------------------------------------

# Sprint 2 – Alembic Configuration

## Objective

Configure Alembic to use the application's central configuration instead of a hardcoded database URL.

## Architecture

```text
.env
    ↓
Application Configuration
    ↓
Alembic
    ↓
PostgreSQL
```

## Benefits

- Single source of truth for database configuration.
- No duplicated connection strings.
- Consistent configuration across FastAPI, tests, and migrations.
- Simplifies environment management for development and production.

-------------------------------------------------------------------

# Sprint 2 – First Database Model

## Objective

Create the first SQLAlchemy model and generate the initial database migration.

## Added

- `User` SQLAlchemy model
- Model registration for Alembic discovery
- Alembic metadata configuration

## User Fields

- `id`
- `email`
- `full_name`
- `hashed_password`
- `is_active`
- `created_at`
- `updated_at`

## Migration Workflow

```text
Model
    ↓
Alembic Revision
    ↓
Migration File
    ↓
Database
```

## Result

The project now manages its database schema through version-controlled migrations instead of manual SQL changes. This establishes the foundation for all future persistent entities.

------------------------------------------------------------------

# Sprint 3 – User Schemas

## Objective

Define the API data contracts for user-related operations.

## Added

- `UserBase`
- `UserCreate`
- `UserResponse`

## Responsibilities

- `UserCreate` validates incoming registration requests.
- `UserResponse` defines the public representation of a user.
- Database models remain internal and are never returned directly to API clients.

## Architecture

```text
Client JSON
      ↓
Pydantic Schema
      ↓
Service
      ↓
Repository
      ↓
Database Model
```

Using dedicated schemas separates API contracts from database implementation and improves security by preventing sensitive fields (such as hashed passwords) from being exposed.

------------------------------------------------------------------

# Sprint 3 – User Repository

## Objective

Implement the data access layer for user-related database operations.

## Added

- `UserRepository`

## Responsibilities

- Retrieve users by email.
- Persist new users.
- Isolate SQLAlchemy operations from business logic.

## Architecture

```text
Service
    ↓
Repository
    ↓
SQLAlchemy
    ↓
PostgreSQL
```

Repositories encapsulate database access, allowing services to focus on business rules while improving maintainability and testability.

-------------------------------------------------------------------

# Sprint 3 – Argon2 Password Hashing

## Objective

Enable the Argon2 password hashing backend used by `pwdlib`.

## Changes

- Installed `pwdlib` with the `argon2` extra.
- Verified password hashing and verification.
- Standardized on Argon2id as the application's password hashing algorithm.

## Security Benefits

- Memory-hard hashing algorithm.
- Resistant to GPU and ASIC attacks.
- Recommended by OWASP for modern web applications.
- Password hashing remains centralized within the security utility layer.


-------------------------------------------------------------------

# Sprint 3 – User Registration API

## Objective

Implement the first complete authentication endpoint for user registration.

## Added Components

- Database session dependency (`get_db`)
- Authentication router
- User registration endpoint
- Router registration in the FastAPI application

## Request Flow

```text
HTTP Request
      ↓
Router
      ↓
AuthService
      ↓
UserRepository
      ↓
PostgreSQL
```

## Endpoint

**POST** `/auth/register`

### Responsibilities

- Validate request data
- Check for duplicate email addresses
- Hash the user's password
- Create a new user record
- Return the public user representation

This is the first end-to-end feature in the backend, connecting HTTP requests to persistent storage through the application's layered architecture.

------------------------------------------------------------------

# Auth Service

## Responsibility

The `AuthService` contains the business logic for user registration.

### Workflow

1. Check if the email is already registered.
2. Raise a domain-specific exception if a duplicate exists.
3. Hash the user's password.
4. Create a `User` model.
5. Persist the user through the repository.

## Design Principle

The service layer contains business rules only. It does not depend on HTTP concepts or SQLAlchemy queries directly. Business-specific failures are represented using custom exceptions instead of generic Python exceptions.

------------------------------------------------------------------

# Sprint 3 – User Registration Endpoint

## Objective

Implement the first complete API endpoint for user registration.

## Components Added

- Database session dependency
- Authentication router
- User registration endpoint

## Request Flow

```text
HTTP Request
      ↓
Router
      ↓
AuthService
      ↓
UserRepository
      ↓
PostgreSQL
```

## Endpoint

**POST** `/auth/register`

### Responsibilities

- Accept registration requests.
- Validate user input.
- Prevent duplicate email registrations.
- Hash passwords securely.
- Store users in PostgreSQL.
- Return a public user representation without exposing sensitive information.

This is the first end-to-end feature of the backend and establishes the foundation for authentication and all user-specific functionality.

-------------------------------------------------------------------

# Sprint 3 – Dependency Injection

## Objective

Refactor the authentication module to use FastAPI's dependency injection system.

## Changes

- Added dependency providers for:
  - Database session
  - User repository
  - Authentication service
- Removed manual object creation from routers.

## Benefits

- Cleaner route handlers.
- Less repetitive code.
- Centralized dependency creation.
- Easier unit testing by allowing dependencies to be overridden.

## Request Flow

HTTP Request
↓
Router
↓
Dependency Injection
↓
Auth Service
↓
Repository
↓
Database

-------------------------------------------------------------------

# Sprint 3 – JWT Token Generation

## Objective

Introduce JSON Web Token (JWT) support for user authentication.

## Added

- JWT utility
- Environment configuration for authentication
- Token generation function

## JWT Payload

```json
{
  "sub": "<user identifier>",
  "exp": "<expiration timestamp>"
}
```

## Configuration

- `SECRET_KEY`
- `ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`

## Purpose

JWT access tokens provide stateless authentication. Once a user successfully logs in, the server issues a signed token that clients include in future requests to access protected resources.

-----------------------------------------------------------------

# Sprint 3 – OAuth2 Login

## Objective

Update the login endpoint to use FastAPI's standard OAuth2 password flow.

## Changes

- Replaced JSON login requests with `OAuth2PasswordRequestForm`.
- Treated the OAuth2 `username` field as the user's email address.
- Enabled full compatibility with Swagger UI's built-in authorization workflow.

## Benefits

- Standards-compliant OAuth2 login.
- Automatic integration with Swagger's **Authorize** button.
- No changes to the database schema or JWT implementation.
- Cleaner developer experience for testing protected endpoints.

# Authentication Refactoring

As the application grows, API schemas should be grouped by domain rather than placed in a single file.

## Planned Organization

- `user.py` — User-related schemas.
- `auth.py` — Authentication and token schemas.
- `chat.py` — Chat request and response schemas.
- `conversation.py` — Conversation schemas.
- `message.py` — Message schemas.

This organization improves maintainability and keeps each module focused on a single domain.

------------------------------------------------------------------

# Sprint 3 Complete – Authentication Foundation

## Completed

- FastAPI application structure
- PostgreSQL integration
- SQLAlchemy ORM
- Alembic migrations
- User model
- Repository pattern
- Service layer
- Password hashing (Argon2)
- JWT authentication
- User registration
- User login
- Protected routes
- Dependency Injection

## Architectural Foundation

The backend now follows a layered architecture:

HTTP Request
↓
Router
↓
Service
↓
Repository
↓
Database

Authentication is complete for Version 1 and provides a secure foundation for all future user-specific features.

## Next Sprint

Implement the conversation system consisting of `Conversation` and `Message` entities. This establishes the data model required for AI chat, conversation history, long-term memory, document retrieval, and autonomous agents.

-------------------------------------------------------------------

# Sprint 4 – Commit 3: Conversation Repository

## Objective

Implement the database access layer for conversations.

## Added

- ConversationRepository
  - create()
  - get_by_id()
  - list_by_user()
  - update()
  - delete()

## Responsibilities

- Execute SQLAlchemy queries
- Commit transactions
- Refresh ORM objects
- Return models to the service layer

## Architecture

Router
    ↓
Service
    ↓
ConversationRepository
    ↓
PostgreSQL

------------------------------------------------------------------

# Sprint 4 – Commit 4: Conversation Service

## Objective

Implement business logic for conversation management.

## Added

- ConversationService
  - create()
  - get_by_id()
  - list_by_user()
  - update()
  - delete()

## Business Rules

- Verify conversation exists
- Verify ownership before access
- Handle conversation updates
- Handle conversation deletion

-------------------------------------------------------------------

# Sprint 4 – Conversation API

## Objective

Expose REST endpoints for managing user conversations.

## Changes

- Added Conversation router.
- Implemented CRUD endpoints for conversations.
- Integrated ConversationService through dependency injection.
- Protected all endpoints using JWT authentication.

## Benefits

- Users can create, retrieve, update, and delete conversations.
- Conversation ownership is validated before every operation.
- Conversation management is accessible through Swagger UI and frontend clients.
- Establishes the API foundation for storing chat history.

# Dependency Injection

The Conversation module follows the application's dependency injection pattern.

## Request Flow

- `conversation.py` — Defines REST endpoints.
- `dependencies.py` — Provides ConversationRepository and ConversationService.
- `ConversationService` — Applies business rules and authorization.
- `ConversationRepository` — Executes database operations.
- `Conversation` model — Persists conversation data.

This keeps routing, business logic, and persistence cleanly separated while ensuring consistent dependency management across the application.

------------------------------------------------------------------

# Sprint 5 – Message Model

## Objective

Introduce the Message entity to store individual chat messages within a conversation.

## Changes

- Added the `Message` database model.
- Established a one-to-many relationship between `Conversation` and `Message`.
- Added an Alembic migration for the `messages` table.
- Configured cascading deletion of messages when a conversation is removed.

## Benefits

- Enables persistent chat history.
- Supports multiple messages per conversation.
- Provides the storage foundation for LLM interactions.
- Prepares the backend for streaming responses, memory, and retrieval features.

# Message Architecture

Each conversation owns multiple messages.

## Relationship

- `Conversation` → One conversation.
- `Message` → Individual user, assistant, or system message.

This design mirrors modern AI chat systems and provides a scalable foundation for future enhancements such as tool calls, attachments, and reasoning traces.

-------------------------------------------------------------------

# Sprint 5 – Message Schemas

## Objective

Define the API schemas for message creation, updates, and responses.

## Changes

- Added `MessageCreate`, `MessageUpdate`, and `MessageResponse` schemas.
- Introduced the `MessageRole` enum for message roles.
- Registered message schemas in the schema package.

## Benefits

- Separates API contracts from database models.
- Prevents invalid message roles through enum validation.
- Provides consistent request and response formats.
- Prepares the API for message CRUD operations.

# Message Validation

Message schemas are responsible for validating incoming and outgoing API data.

## Components

- `MessageCreate` — Validates new message requests.
- `MessageUpdate` — Supports partial message updates.
- `MessageResponse` — Defines the serialized API response.
- `MessageRole` — Restricts roles to `user`, `assistant`, and `system`.

This separation keeps validation logic independent from database models and aligns with the project's layered architecture.

-------------------------------------------------------------------

# Sprint 5 – Message Repository

## Objective

Implement the data access layer for message management.

## Changes

- Added `MessageRepository`.
- Implemented create, retrieve, update, delete, and list operations.
- Added chronological message retrieval for conversations.
- Registered the repository for future dependency injection.

## Benefits

- Encapsulates all database operations for messages.
- Keeps SQLAlchemy logic separate from business logic.
- Provides ordered message history for future LLM requests.
- Maintains consistency with the repository-service architecture.

# Repository Responsibilities

The Message repository is responsible only for persistence.

## Methods

- `create()` — Persist a new message.
- `get_by_id()` — Retrieve a message by ID.
- `list_by_conversation()` — Return conversation history in chronological order.
- `update()` — Save message changes.
- `delete()` — Remove a message.

This separation ensures that business rules remain in the service layer while database operations remain isolated.

-----------------------------------------------------------------

# Sprint 5 – Message Service

## Objective

Implement the business logic layer for message management.

## Changes

- Added `MessageService`.
- Validated conversation existence before creating messages.
- Implemented message retrieval, update, deletion, and conversation history operations.
- Integrated message and conversation repositories through dependency injection.

## Benefits

- Centralizes message-related business logic.
- Prevents creating messages for non-existent conversations.
- Keeps routing independent from persistence logic.
- Prepares the service layer for LLM integration in the next sprint.

# Message Service

The Message service coordinates business rules between conversations and messages.

## Responsibilities

- Validate conversation existence.
- Create messages.
- Retrieve conversation history.
- Update and delete messages.
- Delegate persistence to repositories.

This keeps the application's business logic centralized while maintaining a clean separation from routing and database operations.

------------------------------------------------------------------

# Sprint 6 – LLM Provider Interface

## Objective

Introduce an abstraction layer for language model providers.

## Changes

- Added the `BaseLLMProvider` abstract interface.
- Defined a common `generate()` method for all LLM providers.
- Created the `services/llm` package.

## Benefits

- Decouples business logic from a specific LLM vendor.
- Makes it easy to switch between OpenAI, Anthropic, Gemini, Ollama, or future providers.
- Establishes a scalable architecture for AI integrations.

# LLM Provider Architecture

The application communicates with language models through a common interface.

## Flow

- `ChatService` — Requests text generation.
- `BaseLLMProvider` — Defines the provider contract.
- Provider implementation — Communicates with the selected LLM API.

This design keeps the application independent of any single AI provider and simplifies future integrations.

-------------------------------------------------------------------

# Sprint 6 – Gemini Provider

## Objective

Integrate Google's Gemini API through the provider abstraction.

## Changes

- Added the official Google Gen AI SDK.
- Added Gemini configuration to the application settings.
- Implemented `GeminiProvider`.
- Connected the provider to the shared `BaseLLMProvider` interface.

## Benefits

- Enables AI text generation.
- Keeps the application independent of a specific provider.
- Makes future support for OpenAI, Anthropic, and Ollama straightforward.
- Establishes the foundation for AI-powered conversations.

# LLM Provider

The `GeminiProvider` implements the shared `BaseLLMProvider` interface.

## Flow

- `AIService` requests a response.
- `GeminiProvider` formats the conversation.
- Google Gemini generates the reply.
- The response is returned to the application.

This architecture isolates provider-specific code while keeping business logic provider-agnostic.

-------------------------------------------------------------------

# Sprint 6 – AI Chat Endpoint

## Objective

Expose the first AI-powered chat endpoint backed by Gemini.

## Changes

- Added chat request and response schemas.
- Implemented `AIService` for AI orchestration.
- Added dependency injection for the LLM provider.
- Added `/chat` endpoint.

## Benefits

- End-to-end AI communication through FastAPI.
- Provider-independent architecture.
- Foundation for conversation persistence and memory.

# Request Flow

Client

↓

Chat Router

↓

AIService

↓

GeminiProvider

↓

Gemini API

↓

Response

This milestone establishes the first functional AI interaction within the backend.

-------------------------------------------------------------------

# Sprint 7 – Conversation History

## Objective

Generate AI responses using the complete conversation history.

## Changes

- Added `get_history()` to `MessageService`.
- Formatted conversation history for the LLM provider.
- Updated `AIService` to generate responses from stored messages.

## Benefits

- Enables context-aware conversations.
- Reuses persisted messages instead of relying on transient request data.
- Prepares the backend for storing assistant responses and future memory features.

# AI Pipeline

Current implementation:

1. Validate conversation ownership.
2. Store user message.
3. Load conversation history.
4. Generate AI response.

The generated response is returned to the client but is not yet persisted.

-----------------------------------------------------------------

# Sprint 7 – Persist Assistant Responses

## Objective

Complete the AI conversation pipeline by storing generated assistant responses.

## Changes

- Updated `AIService` to persist assistant messages after generation.
- Completed the end-to-end AI workflow from user input to stored response.
- Ensured both user and assistant messages are retained in PostgreSQL.

## Benefits

- Conversations become fully persistent.
- Enables complete chat history retrieval.
- Provides the foundation for memory, summarization, and retrieval-augmented generation (RAG).

# AI Pipeline

Current implementation:

1. Validate conversation ownership.
2. Store user message.
3. Load conversation history.
4. Generate AI response.
5. Store assistant response.
6. Return response.

The backend now maintains a complete conversation history for every interaction.

------------------------------------------------------------------

