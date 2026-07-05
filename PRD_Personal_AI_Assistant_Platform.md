# Product Requirements Document
# Personal AI Assistant Platform — "Second Brain"

**Version:** 1.0  
**Status:** Draft  
**Last Updated:** June 2026  
**Prepared By:** Product Team  

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Product Vision & Goals](#3-product-vision--goals)
4. [Success Metrics](#4-success-metrics)
5. [User Personas](#5-user-personas)
6. [Platform & Technology Stack](#6-platform--technology-stack)
7. [System Architecture](#7-system-architecture)
8. [Feature Requirements](#8-feature-requirements)
   - 8.1 Authentication & User Management
   - 8.2 AI Chat System
   - 8.3 Personal Memory System
   - 8.4 Notes System
   - 8.5 Document Knowledge Base
   - 8.6 Calendar Integration
   - 8.7 Voice Assistant
   - 8.8 Web Search & Personalized News
   - 8.9 Agent System
   - 8.10 Task Management
   - 8.11 Dashboard
   - 8.12 Global Search
   - 8.13 Smart Notifications & Proactive Suggestions
   - 8.14 Third-Party Integrations
   - 8.15 Offline Mode
   - 8.16 Analytics & Personal Insights
   - 8.17 Data Export & Import
   - 8.18 Multimodal Input
9. [Data Models & Database Schema](#9-data-models--database-schema)
10. [API Design](#10-api-design)
11. [Vector Database Design](#11-vector-database-design)
12. [Caching Strategy](#12-caching-strategy)
13. [LLM Gateway Architecture](#13-llm-gateway-architecture)
14. [Security & Privacy](#14-security--privacy)
15. [Non-Functional Requirements](#15-non-functional-requirements)
16. [Phase 1 Scope](#16-phase-1-scope)
17. [Phased Roadmap](#17-phased-roadmap)
18. [Open Questions & Risks](#18-open-questions--risks)

---

## 1. Executive Summary

The Personal AI Assistant Platform (codename: **"Second Brain"**) is a cross-platform, privacy-first AI companion designed for individuals who want a unified, intelligent system that manages their knowledge, memory, tasks, calendar, documents, and communication from a single interface.

Unlike general-purpose AI chatbots, Second Brain is deeply personalized — it learns about the user over time, connects to their existing tools, and can autonomously execute tasks on their behalf. The system runs entirely on local infrastructure by default, ensuring privacy and data ownership, while providing a migration path to cloud-hosted LLMs as the user grows.

Phase 1 delivers a fully functional MVP targeting personal use and small-scale testing on Web, Android, and iOS (future-ready).

---

## 2. Problem Statement

Modern knowledge workers and developers suffer from severe context fragmentation: their notes live in one app, their tasks in another, their documents in cloud storage, and their conversations are scattered across multiple AI chatbots — none of which remember anything between sessions.

Specific pain points:

- **Memory Loss**: Every AI chat session starts from scratch with zero context about who you are.
- **Tool Sprawl**: Notes, tasks, calendar, documents, and AI are siloed across 5–7 different applications.
- **Privacy Concerns**: Cloud-based AI assistants process all personal data on remote servers without user control.
- **Passive AI**: Current tools answer questions but do not proactively assist, remind, or take actions.
- **No Personal Context**: AI assistants do not know your projects, goals, communication style, or preferences.

---

## 3. Product Vision & Goals

### Vision

> Build a personal AI operating layer that sits above all your tools and data — one that knows you deeply, works for you proactively, and respects your privacy completely.

### Core Goals

| # | Goal | Description |
|---|------|-------------|
| G1 | **Persistent Memory** | The assistant remembers users indefinitely across all sessions |
| G2 | **Unified Knowledge** | Notes, documents, and memories are queryable through one interface |
| G3 | **Calendar Awareness** | The assistant understands your schedule and can manage it |
| G4 | **Voice-First Option** | Full feature parity accessible via voice |
| G5 | **Agentic Execution** | The assistant can execute real tasks, not just answer questions |
| G6 | **Local-First Privacy** | Default to local models and local storage; cloud is opt-in |
| G7 | **Scalable Architecture** | Built modularly for future microservices migration |

---

## 4. Success Metrics

### Phase 1 KPIs

| Metric | Target | Measurement Method |
|--------|--------|--------------------|
| API Response Time | < 2s (non-LLM) | Server-side tracing |
| LLM First Token Latency | < 3s (local models) | Client-side measurement |
| Voice Round-Trip Latency | < 4s (STT + LLM + TTS) | End-to-end timing |
| System Uptime | ≥ 99% during testing | Uptime monitoring |
| Memory Recall Accuracy | ≥ 90% on test queries | Manual test suite |
| RAG Retrieval Relevance | ≥ 85% top-3 match | Human evaluation |
| Mobile App Crash Rate | < 0.5% sessions | Crash reporting |
| Successful OAuth Logins | 100% of test cases | Integration tests |

### Qualitative Metrics

- Users can complete a complex multi-step task via the agent within 5 interactions.
- Users can ask a question about a personal document and receive a grounded, accurate answer.
- Voice mode is usable hands-free without fallback to keyboard.

---

## 5. User Personas

### Persona A — "The Developer" (Primary)
**Name:** Aryan, 27  
**Role:** Full-stack developer  
**Devices:** MacBook, Android phone  
**Pain Points:** Manages multiple side projects, loses context between working sessions, wants an AI that remembers his tech stack and goals  
**Key Features:** Coding help, document RAG, memory system, agent for file/code operations, local LLMs for privacy  

### Persona B — "The Knowledge Worker" (Primary)
**Name:** Priya, 33  
**Role:** Product Manager  
**Devices:** Windows laptop, iPhone  
**Pain Points:** Drowning in meetings, documents, and emails; needs a second brain for recalling decisions and action items  
**Key Features:** Calendar integration, notes, document search, personalized news, daily summary  

### Persona C — "The Researcher / Student" (Secondary)
**Name:** Marcus, 24  
**Role:** Graduate student  
**Devices:** Linux desktop, Android tablet  
**Pain Points:** Needs to organize research papers, synthesize notes, and ask questions about uploaded PDFs  
**Key Features:** Document knowledge base, RAG over PDFs, notes with markdown, voice for hands-free reading  

### Persona D — "The Executive" (Secondary)
**Name:** Sunita, 45  
**Role:** Startup founder  
**Devices:** MacBook, iPhone  
**Pain Points:** Wants proactive briefings, calendar management, and a way to capture ideas on the go via voice  
**Key Features:** Voice assistant, calendar AI, personalized news, proactive daily digest  

---

## 6. Platform & Technology Stack

### Frontend

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Cross-platform Framework | Flutter (Dart) | Single codebase for Web, Android, iOS |
| State Management | Riverpod / BLoC | Scalable reactive state |
| Local Storage (Mobile) | Hive / Isar | Fast offline-first data persistence |
| Audio Processing (Client) | flutter_sound | Push-to-talk recording, audio playback |
| Real-time Chat | WebSocket (dart:io) | Low-latency streaming responses |
| Markdown Rendering | flutter_markdown | Rendering assistant markdown output |

### Backend

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| API Framework | FastAPI (Python 3.11+) | Async, type-safe, fast, excellent AI library support |
| Task Queue | Celery + Redis | Async processing (embeddings, document ingestion) |
| WebSocket Server | FastAPI WebSocket / Starlette | Real-time streaming |
| Auth | JWT + OAuth2 (via Authlib) | Stateless, secure |
| ORM | SQLAlchemy 2.0 (async) | Async-native PostgreSQL access |
| Database | PostgreSQL 15 | Reliable relational store |
| Cache | Redis 7 | Fast caching and pub/sub |
| Vector Database | Qdrant | High-performance vector search |
| File Storage | MinIO (local) / S3 (cloud) | Object storage for documents, audio |

### AI / ML Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Local LLM Runtime | Ollama | Serve Qwen, Llama, Mistral locally |
| Embedding Model | nomic-embed-text / all-MiniLM | Semantic vector generation |
| Speech-to-Text | Whisper (large-v3 or small) | Voice transcription |
| Text-to-Speech | Piper (local) / Coqui TTS | Voice response synthesis |
| Agent Orchestration | LangChain / custom ReAct loop | Tool-calling agent framework |

### Infrastructure (Local/Self-Hosted)

| Component | Technology |
|-----------|-----------|
| Containerization | Docker + Docker Compose |
| Reverse Proxy | Nginx |
| Secret Management | .env + python-decouple |
| Monitoring | Prometheus + Grafana |
| Logging | Structlog + ELK or Loki |
| CI/CD | GitHub Actions |

---

## 7. System Architecture

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                               │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│   │  Web (Flutter│    │Android App  │    │  iOS App (Future)   │  │
│   │    Web)      │    │(Flutter)    │    │  (Flutter)          │  │
│   └──────┬──────┘    └──────┬──────┘    └──────────┬──────────┘  │
└──────────┼──────────────────┼───────────────────────┼────────────┘
           │ HTTPS / WebSocket│                        │
┌──────────▼──────────────────▼───────────────────────▼────────────┐
│                         GATEWAY LAYER                             │
│              Nginx Reverse Proxy + Rate Limiter                   │
└──────────────────────────┬────────────────────────────────────────┘
                           │
┌──────────────────────────▼────────────────────────────────────────┐
│                        API LAYER (FastAPI)                        │
│                                                                   │
│  ┌─────────┐ ┌────────┐ ┌────────┐ ┌─────────┐ ┌─────────────┐  │
│  │  Auth   │ │  Chat  │ │ Memory │ │  Notes  │ │  Documents  │  │
│  │ Service │ │Service │ │Service │ │ Service │ │   Service   │  │
│  └─────────┘ └────────┘ └────────┘ └─────────┘ └─────────────┘  │
│  ┌─────────┐ ┌────────┐ ┌────────┐ ┌─────────┐ ┌─────────────┐  │
│  │Calendar │ │ Voice  │ │ Agent  │ │  Task   │ │   Search    │  │
│  │ Service │ │Service │ │Service │ │ Service │ │   Service   │  │
│  └─────────┘ └────────┘ └────────┘ └─────────┘ └─────────────┘  │
│  ┌─────────┐ ┌──────────────────────┐                            │
│  │  News   │ │   Notification       │                            │
│  │ Service │ │      Service         │                            │
│  └─────────┘ └──────────────────────┘                            │
└──────────────────────────┬────────────────────────────────────────┘
                           │
┌──────────────────────────▼────────────────────────────────────────┐
│                     INTELLIGENCE LAYER                            │
│                                                                   │
│   ┌─────────────────────────────────────────────────────────┐    │
│   │                    LLM GATEWAY                          │    │
│   │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐  │    │
│   │  │  Ollama │ │  GPT-4  │ │  Claude │ │   Gemini    │  │    │
│   │  │(Qwen/   │ │(Future) │ │(Future) │ │  (Future)   │  │    │
│   │  │Llama/   │ └─────────┘ └─────────┘ └─────────────┘  │    │
│   │  │Mistral) │                                            │    │
│   │  └─────────┘                                            │    │
│   └─────────────────────────────────────────────────────────┘    │
│   ┌──────────────────┐  ┌─────────────────────────────────────┐  │
│   │  RAG Pipeline    │  │    Agent Executor (ReAct Loop)      │  │
│   │  Chunker+Embedder│  │    Tool Registry + Safety Layer     │  │
│   └──────────────────┘  └─────────────────────────────────────┘  │
└──────────────────────────┬────────────────────────────────────────┘
                           │
┌──────────────────────────▼────────────────────────────────────────┐
│                       DATA LAYER                                  │
│                                                                   │
│  ┌────────────────┐  ┌──────────────┐  ┌───────────────────────┐ │
│  │  PostgreSQL 15 │  │   Redis 7    │  │    Qdrant Vector DB   │ │
│  │  (Primary DB)  │  │  (Cache/PubSub│  │  (Documents/Notes/   │ │
│  └────────────────┘  └──────────────┘  │    Memories)         │ │
│  ┌────────────────────────────────┐    └───────────────────────┘ │
│  │     MinIO / S3-Compatible      │                              │
│  │  (Files, Avatars, Audio Files) │                              │
│  └────────────────────────────────┘                              │
└──────────────────────────────────────────────────────────────────┘
```

### Request Lifecycle

1. Client sends HTTPS request → Nginx validates TLS, rate-limits
2. FastAPI validates JWT, resolves user context
3. Service handler processes request
4. LLM Gateway selects and routes to appropriate model
5. Context is assembled: user memory + RAG retrieval + conversation history
6. LLM generates response (streamed via SSE / WebSocket)
7. Response stored in DB, memory extracted if needed
8. Client renders streamed tokens in real time

---

## 8. Feature Requirements

---

### 8.1 Authentication & User Management

#### 8.1.1 OAuth Providers

The system supports exclusively OAuth-based authentication. No username/password login.

| Provider | Scopes Required |
|----------|----------------|
| Google OAuth 2.0 | openid, email, profile, calendar (optional) |
| Apple Sign-In | name, email |
| Microsoft OAuth 2.0 | openid, email, profile, Calendars.ReadWrite (optional) |

#### 8.1.2 Auth Flow

```
User → "Sign in with Google" → Redirect to Google OAuth → 
Callback with auth code → Backend exchanges for tokens → 
JWT issued → Stored in secure client storage
```

- Access Token lifetime: 1 hour
- Refresh Token lifetime: 30 days (sliding expiration)
- Refresh tokens stored server-side (revocable)
- All OAuth secrets encrypted at rest (AES-256)

#### 8.1.3 User Profile

```
Users Table:
- id (UUID)
- email (unique)
- name
- avatar_url
- provider (google | apple | microsoft)
- provider_id
- created_at
- last_login_at
- is_active
- is_verified
```

#### 8.1.4 Session Management

- Multiple active sessions supported (web + mobile simultaneously)
- Session list visible in settings
- Users can revoke individual sessions
- Suspicious login detection (new device/location → notification)

#### 8.1.5 Account Deletion

- User can request full account deletion
- 30-day deactivation grace period
- All user data purged: DB records, vectors, files, cache entries
- Export available before deletion (see 8.17)

---

### 8.2 AI Chat System

#### 8.2.1 Chat Session Management

Users can:
- Create new chat sessions
- Rename chat sessions (manual or AI-suggested title)
- Delete individual chats (soft-delete with 30-day recovery)
- Archive chats
- Pin important chats (max 5)
- Search across all chat history
- Export individual chat as Markdown or PDF

#### 8.2.2 Message Features

Each message supports:
- Plain text input
- Markdown rendering (code blocks, tables, lists)
- Code syntax highlighting (50+ languages)
- LaTeX math rendering (via KaTeX)
- File attachments inline (images, PDFs for context)
- Message editing (user messages — triggers re-generation)
- Message deletion
- Message reactions (thumbs up/down for quality feedback)
- Copy to clipboard
- Message threading (reply to a specific message)
- Token count display per message

#### 8.2.3 Streaming

- Server-Sent Events (SSE) for streaming LLM output token-by-token
- Visual typing indicator during generation
- Stop generation button
- Regenerate last response button

#### 8.2.4 Context Assembly

The AI receives context assembled in this order:

```
[System Prompt]
  ↓
[User Long-Term Memory Summary] (top-K relevant memories)
  ↓
[Relevant RAG Chunks] (from documents, notes if enabled)
  ↓
[Conversation History] (last N messages, trimmed to fit context window)
  ↓
[Current User Message]
```

Context window management:
- Track token usage per model
- Automatically summarize older conversation parts when approaching limit
- Display token usage indicator in UI (optional)

#### 8.2.5 Chat Modes

| Mode | Description |
|------|-------------|
| General Chat | Default conversational assistant |
| Document Chat | RAG enabled over selected documents |
| Code Mode | Coding assistant with code execution hints |
| Focus Mode | Minimal UI, distraction-free, no memory injection |
| Brainstorm Mode | More creative/exploratory LLM parameters |

#### 8.2.6 Suggested Prompts

- Show 3 contextual suggested prompts on new chat (based on time of day, recent activity)
- Examples: "Continue working on [recent project]", "What's on my calendar today?"

#### 8.2.7 AI Capabilities

The assistant can perform:
- General conversation and Q&A
- Code writing, debugging, and review
- Text summarization and rewriting
- Brainstorming and ideation
- Document analysis (with RAG)
- Research synthesis
- Calendar operations (via Calendar Service)
- Task creation (via Task Service)
- Web search (when enabled)
- Agent actions (via Agent Service)

---

### 8.3 Personal Memory System

#### 8.3.1 Memory Architecture

Three tiers of memory:

| Tier | Scope | Storage | TTL |
|------|-------|---------|-----|
| Working Memory | Current turn context window | In-memory | Request lifetime |
| Session Memory | Current conversation | Redis | 24 hours |
| Long-Term Memory | Persistent user facts | PostgreSQL + Qdrant | Permanent |

#### 8.3.2 Memory Schema

```
Memories Table:
- id (UUID)
- user_id (FK)
- category (preference | fact | project | interest | relationship | goal | habit)
- title (short summary)
- content (full memory text)
- source (auto | manual | chat_id)
- embedding_id (Qdrant reference)
- confidence_score (0.0–1.0)
- access_count
- last_accessed_at
- created_at
- updated_at
- is_verified (user confirmed)
- tags (array)
```

#### 8.3.3 Automatic Memory Extraction

After each chat session (async, background job):
- LLM analyzes conversation for extractable facts
- Candidate memories presented to user for confirmation (or auto-saved based on setting)
- Deduplication against existing memories using semantic similarity
- Conflicting memories flagged for user resolution

Examples of auto-extracted memories:
- "User prefers Python over JavaScript"
- "User is building a SaaS product in the fintech space"
- "User's wife is named Ananya"
- "User wakes up at 6 AM and exercises daily"

#### 8.3.4 Memory Categories

| Category | Examples |
|----------|---------|
| Preferences | Language preferences, dark mode, communication style |
| Facts | Name, location, job, family |
| Projects | Active projects, tech stacks, goals |
| Interests | Topics, hobbies, books, media |
| Relationships | People user mentions regularly |
| Goals | Short-term and long-term objectives |
| Habits | Daily routines, work schedule |
| Medical / Health (opt-in) | Dietary restrictions, fitness goals |

#### 8.3.5 Memory Management UI

- Searchable memory list with category filters
- Memory cards with edit / delete / verify actions
- Memory import from JSON
- Memory strength indicator (based on access frequency)
- Memory privacy settings (exclude certain categories from LLM context)
- "Forget this" option for sensitive topics

#### 8.3.6 Memory Retrieval in Context

- Top-K semantic search via Qdrant at query time
- Relevance scoring combines semantic similarity + recency + access frequency
- Maximum 10 memory items injected per request (configurable)
- Memory injection toggle (user can disable per-chat)

---

### 8.4 Notes System

#### 8.4.1 Note Features

Users can:
- Create, edit, delete, and restore notes
- Organize notes with folders and tags
- Pin important notes
- View notes in list or card grid view
- Sort by: date created, date modified, title, tag

#### 8.4.2 Note Types & Editor

| Type | Description |
|------|-------------|
| Plain Text | Simple text editor |
| Markdown | Full GFM markdown with live preview |
| Rich Text | WYSIWYG editor (bold, italic, lists, headers) |
| Quick Capture | Streamlined minimal input, no friction |
| Voice Note | Record audio → auto-transcribed to text via Whisper |
| AI-Generated | Notes created or expanded by AI |

Editor features:
- Auto-save every 5 seconds
- Version history (last 20 versions)
- Word count and reading time
- Inline AI commands: `/improve`, `/summarize`, `/expand`, `/translate`
- Insert from AI: user types "AI, write a meeting summary for today"

#### 8.4.3 Note Organization

- Folders with nesting (max 3 levels deep)
- Tags (multi-tag support, autocomplete)
- Smart Collections (auto-grouped by: recent, starred, by-date, by-tag)
- Trash with 30-day auto-purge

#### 8.4.4 Note Search

- Full-text search across title and body
- Tag-based filtering
- Semantic search ("find my notes about machine learning architectures")
- Date range filters
- Results highlight matched terms

#### 8.4.5 Note Embeddings

All notes are vectorized and stored in Qdrant for:
- Semantic search
- RAG retrieval in chat ("based on my notes about X…")
- Auto-linking related notes (AI-suggested)
- Memory extraction from notes

---

### 8.5 Document Knowledge Base

#### 8.5.1 Supported Formats

| Format | Processing Method |
|--------|------------------|
| PDF | PyMuPDF / pdfplumber — text + layout extraction |
| DOCX | python-docx — structured text extraction |
| TXT | Direct ingestion |
| MD | Markdown-aware chunking |
| CSV | Tabular-aware chunking with row context |
| EPUB (Phase 2) | ebooklib extraction |
| Web URL (Phase 2) | Crawl4AI / BeautifulSoup ingestion |

#### 8.5.2 Document Ingestion Pipeline

```
Upload (S3/MinIO)
        │
        ▼
Text Extraction
(format-specific parser)
        │
        ▼
Metadata Extraction
(title, author, date, page count)
        │
        ▼
Smart Chunking
(recursive character splitting, 512 tokens, 50-token overlap)
        │
        ▼
Chunk Embedding
(nomic-embed-text via Ollama, batch=32)
        │
        ▼
Vector Upsert (Qdrant)
+ Chunk Storage (PostgreSQL)
        │
        ▼
Index Updated → User Notified
```

Processing is asynchronous via Celery. Users see processing status indicator.

#### 8.5.3 Document Schema

```
Documents Table:
- id (UUID)
- user_id (FK)
- filename
- display_name
- format (pdf | docx | txt | md | csv)
- file_size_bytes
- storage_path (MinIO/S3 key)
- page_count
- word_count
- status (uploading | processing | ready | failed)
- error_message
- metadata (JSONB: title, author, date, custom tags)
- created_at
- updated_at
- last_accessed_at

DocumentChunks Table:
- id (UUID)
- document_id (FK)
- chunk_index
- content (text)
- page_number
- token_count
- embedding_id (Qdrant reference)
```

#### 8.5.4 RAG Query Flow

```
User Query
     │
     ▼
Query Embedding
     │
     ▼
Qdrant Semantic Search
(user-scoped collection, top-K=5)
     │
     ▼
Chunk Reranking
(cross-encoder reranker for precision)
     │
     ▼
Context Assembly
(inject top chunks into LLM prompt with citations)
     │
     ▼
LLM Generation
(grounded answer with source references)
     │
     ▼
Response with Citations
(document name + page number shown to user)
```

#### 8.5.5 Document Chat

- Chat scoped to one or more selected documents
- Source citations shown: "[Source: Kubernetes_Guide.pdf, p.34]"
- Confidence indicator per answer
- "View source" opens document at relevant page/section
- Multi-document comparison: "Compare my two architecture documents"

#### 8.5.6 Document Management

- Folder organization same as Notes system
- Document preview (first 3 pages rendered)
- Re-process document (if parsing improved)
- Share document context (generate shareable read-only link — Phase 2)
- Storage quota tracking per user (default: 2GB)

---

### 8.6 Calendar Integration

#### 8.6.1 Supported Providers

| Provider | API | Scopes |
|----------|-----|--------|
| Google Calendar | Google Calendar API v3 | calendar.readonly, calendar.events |
| Microsoft Outlook | Microsoft Graph API | Calendars.ReadWrite |
| Apple Calendar (Phase 2) | CalDAV | Read + Write |

#### 8.6.2 Calendar Schema

```
CalendarAccounts Table:
- id (UUID)
- user_id (FK)
- provider (google | microsoft | apple)
- account_email
- access_token_encrypted
- refresh_token_encrypted
- token_expires_at
- is_primary
- sync_enabled
- last_synced_at

CalendarEvents Table (local cache):
- id (UUID)
- calendar_account_id (FK)
- external_event_id
- title
- description
- location
- start_datetime
- end_datetime
- is_all_day
- recurrence_rule
- attendees (JSONB)
- status (confirmed | tentative | cancelled)
- synced_at
- created_by (user | ai)
```

#### 8.6.3 Sync Strategy

- Full sync on first connection
- Incremental sync every 15 minutes (background job)
- Real-time sync on event creation/edit via push notifications (Google/Microsoft support)
- Conflict resolution: external calendar is source of truth; local-only events sync outward

#### 8.6.4 Calendar Views

| View | Description |
|------|-------------|
| Day View | Hourly timeline for today |
| Week View | 7-day grid |
| Month View | Calendar grid |
| Agenda View | Chronological list of upcoming events |
| AI Briefing | Natural language summary of the day/week |

#### 8.6.5 AI Calendar Features

| Action | Example Prompt |
|--------|----------------|
| Create Event | "Schedule a team sync tomorrow at 3 PM for 1 hour" |
| Find Free Time | "When am I free on Thursday afternoon?" |
| Reschedule | "Move my 4 PM meeting to Friday at the same time" |
| Cancel Event | "Cancel my dentist appointment on June 10th" |
| Smart Scheduling | "Find a 2-hour block this week for deep work" |
| Meeting Prep | "What do I have before my 3 PM today?" |
| Conflict Detection | "Do I have any conflicts next week?" |
| Travel Buffer | "Add 30 minutes travel before my 2 PM" |

All destructive calendar actions (cancel, delete) require explicit user confirmation.

#### 8.6.6 Event Intelligence

- Auto-detect meeting type from title (video call, in-person, focus block)
- Extract meeting links (Zoom, Google Meet, Teams) and display prominently
- Suggest meeting prep time for events with > 3 attendees
- Smart notification timing based on travel distance (Phase 2)

---

### 8.7 Voice Assistant

#### 8.7.1 Voice Pipeline

```
User speaks
     │
     ▼
Audio Captured (client-side)
16kHz, mono, PCM/WebM
     │
     ▼
VAD (Voice Activity Detection)
Silero VAD or WebRTC VAD
     │
     ▼
Audio → Server (WebSocket stream)
     │
     ▼
Whisper STT (faster-whisper or whisper.cpp)
Language auto-detection or user-set preference
     │
     ▼
Text → Chat Pipeline
(memory + RAG + LLM as normal)
     │
     ▼
Response Text → Piper TTS
(voice cloning optional in Phase 2)
     │
     ▼
Audio Stream → Client
     │
     ▼
Audio Playback
```

#### 8.7.2 Voice Models

| Component | Model Options | Notes |
|-----------|--------------|-------|
| STT | whisper-small, whisper-medium, whisper-large-v3 | Trade-off: speed vs accuracy |
| TTS | Piper (en_US-lessac-high, en_IN-*) | 16kHz, runs locally |
| VAD | Silero VAD | Prevents silence → empty API calls |

#### 8.7.3 Voice Input Modes

| Mode | Description | Default |
|------|-------------|---------|
| Push-to-Talk | Hold button → record → release → send | Default |
| Continuous Listening | Always-on, VAD-controlled | Opt-in |
| Wake Word | "Hey Aria" triggers activation (Phase 2) | Phase 2 |

#### 8.7.4 Voice Settings

User can configure:
- TTS voice (select from available Piper voices)
- TTS speed (0.75× to 1.5×)
- STT language (auto-detect or manual)
- Auto-play response audio (on/off)
- Push-to-talk key binding (keyboard shortcut for desktop web)
- Voice response length (brief / normal / detailed)

#### 8.7.5 Voice Notes

- Dedicated "Voice Note" mode: record → transcribe → save as note
- Transcription shown alongside playback of original audio
- Edit transcription before saving
- Background transcription (upload audio → get transcript later)

#### 8.7.6 Multilingual Voice

- STT supports 90+ languages via Whisper
- Response in same language as input (auto-detect)
- TTS voice changes to match language if supported by Piper
- Language preference can be pinned in settings

---

### 8.8 Web Search & Personalized News

#### 8.8.1 Web Search

Search is exposed as a tool available to the AI agent and can be triggered:
- Explicitly: "Search the web for latest updates on Llama 4"
- Automatically: When AI detects a question requiring current information

**Search Engine Integration:**
- Primary: SearXNG (self-hosted, privacy-preserving meta-search)
- Fallback: Brave Search API or Serper API

**Search Features:**
- Query formulation by LLM (query optimization)
- Top 10 result URLs fetched and scraped
- Content extracted, chunked, summarized by LLM
- Final response with cited sources
- Safe search filtering

**Search Result Schema:**
```
- title
- url
- snippet
- full_content (scraped)
- relevance_score
- published_date
- domain
```

#### 8.8.2 Personalized News

**User Interest Configuration:**
- Users define up to 20 interest categories
- Predefined: AI & ML, Technology, Finance, Startups, Science, Health, Politics, Sports, Entertainment
- Custom categories: any free-text topic
- Per-interest: enable/disable, priority weighting

**News Digest Generation:**
- Runs daily at user's preferred time (configurable, default: 8 AM local time)
- Aggregates from RSS feeds + search for each interest
- LLM generates cohesive summary (not just headlines)
- Deduplicates stories across sources
- Shows confidence/sentiment indicator per story
- Full article available via "Read More" (opens in-app browser)

**News Sources:**
- Built-in curated RSS feed list per category
- User can add custom RSS feeds
- Source trustworthiness indicator
- Filter by region (global, regional, local)

**News Digest Schema:**
```
NewsDigests Table:
- id (UUID)
- user_id (FK)
- date
- summary_text (LLM-generated overview)
- articles (JSONB array)
- interests_covered (array)
- generated_at
- was_read
```

---

### 8.9 Agent System

#### 8.9.1 Agent Architecture

The agent uses a **ReAct (Reasoning + Acting)** loop:

```
User Goal
     │
     ▼
Planner (LLM): Break goal into steps
     │
     ▼
Step Executor: Select tool → execute → observe result
     │
     ▼
Memory Updater: Record action + result
     │
     ▼
Evaluator: Goal achieved? If not → loop; if yes → respond
```

Maximum loop depth: 10 steps (configurable, safety limit).

#### 8.9.2 Phase 1 Agent Tools

| Tool | Description | Confirmation Required |
|------|-------------|----------------------|
| `open_application` | Launch app by name | No |
| `open_url` | Open URL in browser | No |
| `read_file` | Read file content from disk | No |
| `create_file` | Create new file with content | No |
| `edit_file` | Modify existing file | Yes |
| `delete_file` | Delete file permanently | Yes (with preview) |
| `list_directory` | List folder contents | No |
| `run_command` | Execute shell command | Yes (show command first) |
| `web_search` | Search the web | No |
| `calendar_create` | Create calendar event | Yes |
| `calendar_delete` | Delete calendar event | Yes |
| `task_create` | Create new task | No |
| `send_notification` | Send system notification | No |
| `take_screenshot` | Capture screen | Yes |

#### 8.9.3 Safety System

- **Pre-execution review**: Agent presents plan before executing any destructive action
- **Sandboxed execution**: Shell commands run in restricted environment (no root, no network by default)
- **Allowlist/Blocklist**: Users define allowed directories and blocked commands
- **Audit log**: Every agent action logged with timestamp, tool used, input, output
- **Rollback**: File operations generate backups (configurable retention)
- **Emergency stop**: User can halt agent mid-execution

#### 8.9.4 Agent Memory

The agent maintains its own short-term scratchpad (distinct from user memory):
- Task decomposition steps
- Intermediate results
- Failed attempts and retry strategies
- Cleared on task completion

#### 8.9.5 Multi-Step Task Examples

- "Draft a Python script to scrape Hacker News top 10, save it to my Desktop, and create a calendar reminder to run it every Monday morning"
- "Summarize the PDF I uploaded yesterday and create a task to send it to my team by Friday"
- "Find the latest news on OpenAI, write a brief, and save it as a note tagged 'AI News'"

---

### 8.10 Task Management

#### 8.10.1 Task Schema

```
Tasks Table:
- id (UUID)
- user_id (FK)
- title (required)
- description (optional, markdown)
- status (todo | in_progress | done | cancelled)
- priority (low | medium | high | urgent)
- due_date (optional)
- reminder_at (optional)
- project_id (FK, optional)
- parent_task_id (FK, optional — subtasks)
- tags (array)
- created_by (user | ai | agent)
- created_at
- updated_at
- completed_at
- recurrence_rule (optional)
- estimated_minutes (optional)
- actual_minutes (optional)
```

#### 8.10.2 Task Views

| View | Description |
|------|-------------|
| Today | Tasks due today + overdue |
| Inbox | All unscheduled tasks |
| Upcoming | Tasks by due date (next 7/14/30 days) |
| Projects | Grouped by project |
| Kanban Board | Drag-drop: Todo / In Progress / Done |
| Completed | Archive of done tasks |

#### 8.10.3 AI Task Features

| Feature | Example |
|---------|---------|
| Natural language creation | "Remind me to submit the report by next Friday at 5 PM" |
| Smart prioritization | AI suggests priority based on due date + context |
| Subtask generation | "Break down 'Launch landing page' into subtasks" |
| Time estimation | AI estimates effort based on task description |
| Task from chat | Any chat message can be converted to task with one click |
| Weekly review | AI generates weekly task summary every Sunday |

#### 8.10.4 Projects

- Group tasks into named projects
- Project color coding
- Project-level progress indicator
- Project notes linked to project
- Archive completed projects

---

### 8.11 Dashboard

#### 8.11.1 Dashboard Components

The dashboard is the default landing view and surfaces the most important information:

| Widget | Description | Configurable |
|--------|-------------|-------------|
| Today's Briefing | AI-written daily summary (calendar + tasks + news) | Yes |
| Calendar Today | Today's events timeline | Yes |
| Tasks: Due Today | Tasks due today or overdue | Yes |
| Recent Notes | Last 5 modified notes | Yes |
| Recent Documents | Last 3 accessed documents | Yes |
| Memories | 3 recently saved or surfaced memories | Yes |
| News Digest | Top 3 headlines from user's interests | Yes |
| Quick Capture | One-tap note, task, or voice input | Yes |
| AI Suggestions | Proactive suggestions from AI | Yes |
| Productivity Streak | Days of daily usage (gamification) | Optional |

#### 8.11.2 Dashboard Customization

- Drag-and-drop widget reordering
- Show/hide individual widgets
- Widget size (compact / normal / expanded)
- Separate dashboard layouts for mobile vs desktop
- Custom greeting (user name + time-aware)

#### 8.11.3 Daily Briefing

Generated at user's configured morning time (default 8 AM):

```
Good morning, Aryan! Here's your day:

📅 You have 3 meetings today:
   → 10:00 AM: Product sync (45 min, Google Meet)
   → 2:00 PM: 1:1 with Sarah
   → 4:30 PM: Interview: Backend Engineer

✅ Tasks due today:
   → Submit PR for auth service (High)
   → Review design mockups

📰 Top news:
   → GPT-5 announced with multi-modal reasoning
   → YC W26 batch applications open

💡 AI Suggestion:
   You have a 90-minute free block from 11 AM – 12:30 PM.
   Your deepest focus time — consider tackling "Submit PR for auth service."
```

---

### 8.12 Global Search

#### 8.12.1 Search Architecture

Global search provides a single unified entry point across all user data:

```
User Query
     │
     ├──► Full-Text Search (PostgreSQL FTS)
     │    → Notes, Chats, Tasks, Documents (titles)
     │
     ├──► Semantic Search (Qdrant)
     │    → Notes, Documents, Memories, Chats
     │
     └──► Metadata Filter Search
          → Calendar events (date range), Tasks (status, priority)
```

Results are merged, deduplicated, and ranked by a combined relevance score.

#### 8.12.2 Search Features

- Live search (results appear as user types, debounced 300ms)
- Universal search shortcut (Cmd+K / Ctrl+K)
- Source filtering: toggle Notes / Documents / Chats / Tasks / Memories / Calendar
- Date range filter
- Sort by: relevance, date, type
- Search history (last 50 searches, clearable)
- Save search as a named bookmark
- Semantic search toggle ("smart search")

#### 8.12.3 Result Types

Each result card shows:
- Type icon (note, document, chat, task, memory)
- Title
- Snippet with highlighted matched terms
- Date
- Source (for documents: filename + page)
- Quick action button (open, edit, chat)

---

### 8.13 Smart Notifications & Proactive Suggestions

#### 8.13.1 Notification Types

| Type | Trigger | Example |
|------|---------|---------|
| Task Reminder | Due date approaching | "Report due in 2 hours" |
| Calendar Alert | Event starting soon | "Meeting starts in 15 min" |
| Daily Briefing | Morning (configured time) | Today's digest |
| Memory Surface | AI detects relevant memory | "You mentioned X last week" |
| AI Suggestion | Context-based proactive help | "You have 2 hours free — continue your deep work?" |
| News Digest | Scheduled delivery | Daily news summary |
| Agent Confirmation | Action needs approval | "Agent wants to run: rm -rf..." |
| Streak | Habit tracking | "5-day usage streak!" |
| Memory Confirmation | New memory extracted | "I noticed: You prefer TypeScript. Save?" |

#### 8.13.2 Notification Channels

| Channel | Platform |
|---------|----------|
| In-App Notification | All platforms |
| Push Notification | Android, iOS |
| Desktop Notification | Web (via Notification API) |
| Email Digest (opt-in) | All platforms |

#### 8.13.3 Proactive AI Suggestions

The assistant generates proactive suggestions based on:

- **Time of day**: Morning → "Review today's schedule?"; Evening → "Daily reflection?"
- **Calendar gaps**: Large free blocks → suggest deep work tasks
- **Task deadlines**: Tasks due soon without progress → surface them
- **Inactivity**: Topic not revisited in N days → "You haven't worked on [project] in a week"
- **Memory-triggered**: Upcoming date matches a remembered event → "Your mom's birthday is in 3 days"

Suggestions shown as dismissible cards on Dashboard and optionally sent as push notifications.

#### 8.13.4 Notification Preferences

User controls:
- Per-type enable/disable
- Do Not Disturb schedule (e.g., 10 PM – 7 AM)
- Notification frequency (immediate, batched hourly, daily digest only)
- Quiet weekend mode

---

### 8.14 Third-Party Integrations

#### 8.14.1 Phase 1 Integrations

| Integration | Feature | Method |
|-------------|---------|--------|
| Google Calendar | Read/write events | OAuth + API |
| Microsoft Calendar | Read/write events | OAuth + Graph API |
| Google Drive (Phase 2) | Import documents | OAuth + API |
| Notion (Phase 2) | Import notes | OAuth + API |
| GitHub (Phase 2) | Code context, PRs | OAuth + API |

#### 8.14.2 Integration Framework

All integrations are implemented as pluggable **Connector** modules:

```
BaseConnector (abstract)
├── authenticate()
├── sync()
├── disconnect()
└── handle_webhook()

GoogleCalendarConnector(BaseConnector)
MicrosoftCalendarConnector(BaseConnector)
GoogleDriveConnector(BaseConnector) [Phase 2]
```

Each connector:
- Has its own credential storage (encrypted)
- Supports manual or scheduled sync
- Emits standardized internal events consumed by relevant services
- Can be disabled without data loss

#### 8.14.3 Webhook Support

External services push updates via webhooks where supported:
- Google Calendar: Push notifications via Google Pub/Sub
- Microsoft: Graph API change notifications
- Received, validated, and processed within 500ms

---

### 8.15 Offline Mode

#### 8.15.1 Offline Capabilities (Mobile)

| Feature | Offline Behavior |
|---------|-----------------|
| View notes | ✅ Available (local cache) |
| Edit notes | ✅ Local edits queued for sync |
| View tasks | ✅ Available (local cache) |
| Edit tasks | ✅ Local edits queued for sync |
| View calendar | ✅ Cached events (up to 30 days) |
| View recent chats | ✅ Available (local cache) |
| New chat (AI) | ❌ Requires connection (local Ollama exception: possible via device LLM in Phase 2) |
| Search | ⚠️ Local full-text only (no semantic) |
| Voice recording | ✅ Record locally, transcribe when online |

#### 8.15.2 Sync Strategy

- Optimistic UI: local changes applied instantly, synced in background
- Conflict resolution: last-write-wins with timestamp comparison; user prompted for manual conflicts
- Sync queue stored in local Isar/Hive DB
- Auto-sync on reconnect
- Sync status indicator (synced / syncing / conflict / offline)

---

### 8.16 Analytics & Personal Insights

#### 8.16.1 Productivity Insights

A personal analytics dashboard showing:

| Metric | Display |
|--------|---------|
| Tasks completed per week | Bar chart |
| Focus time (calendar blocks) | Weekly trend |
| Note creation frequency | Activity heatmap |
| Most used topics (chat, notes) | Word cloud / tag cloud |
| Longest streak | Milestone badge |
| Most productive time of day | Based on task completion timestamps |
| AI usage patterns | Calls per day, top features used |

#### 8.16.2 Memory Insights

- Total memories stored
- Memory categories breakdown (donut chart)
- Most frequently accessed memories
- Memory growth over time

#### 8.16.3 Storage Insights

- Documents: count, total size, formats
- Notes: count, word count
- Audio: recordings stored
- Total storage used vs quota

All analytics are computed locally or server-side — never sent to third parties.

---

### 8.17 Data Export & Import

#### 8.17.1 Export

Users can export all personal data in standard formats:

| Data Type | Export Format |
|-----------|--------------|
| Chats | JSON, Markdown |
| Notes | Markdown, JSON, ZIP folder |
| Tasks | JSON, CSV |
| Memories | JSON |
| Documents | Original files ZIP |
| Calendar Events | ICS |
| User Profile | JSON |
| All Data | Full ZIP archive |

- Export initiated from Settings > Data > Export
- Large exports are async (user notified when ready)
- Download link expires in 24 hours
- Export includes a README explaining the data structure

#### 8.17.2 Import

| Source | Format | Supported |
|--------|--------|-----------|
| Own Export | ZIP (Second Brain format) | Phase 1 |
| Obsidian Vault | ZIP of Markdown files | Phase 1 |
| Notion Export | ZIP (Markdown + CSV) | Phase 2 |
| Apple Notes | Export folder | Phase 2 |
| Roam Research | JSON | Phase 2 |

Import pipeline: upload → parse → deduplicate → preview → confirm → ingest

#### 8.17.3 GDPR Compliance

- Right to access: export all data
- Right to erasure: full account deletion removes all data within 30 days
- Data portability: standard format exports
- Consent management: clear per-feature data collection disclosure

---

### 8.18 Multimodal Input

#### 8.18.1 Image Understanding

Users can attach images to chat messages:
- Screenshots for debugging / explanation
- Whiteboard photos for extraction
- Charts / graphs for analysis
- Screenshots of errors / logs

Backend: Uses vision-capable models (LLaVA via Ollama for local; GPT-4o / Claude for cloud).

#### 8.18.2 Screen Capture (Desktop Web / Agent)

- User can trigger screen capture via agent
- Screenshot analyzed by vision model
- Used for: bug reporting, visual task extraction, UI feedback

#### 8.18.3 File Attachments in Chat

| Type | Size Limit | Handling |
|------|------------|----------|
| Images (jpg, png, webp) | 10MB | Vision model |
| PDFs | 20MB | Extract text → inject context |
| DOCX | 10MB | Extract text → inject context |
| TXT / MD | 1MB | Direct injection |
| Audio | 25MB | Whisper transcription |
| Code files | 1MB | Syntax highlight + inject |

---

## 9. Data Models & Database Schema

### Core Table Overview

```sql
-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    avatar_url TEXT,
    provider VARCHAR(20) NOT NULL CHECK (provider IN ('google', 'apple', 'microsoft')),
    provider_id VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ
);

-- User Preferences
CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    theme VARCHAR(10) DEFAULT 'dark' CHECK (theme IN ('dark', 'light', 'system')),
    preferred_llm VARCHAR(50) DEFAULT 'llama3.2',
    tts_voice VARCHAR(100) DEFAULT 'en_US-lessac-high',
    tts_speed DECIMAL(3,2) DEFAULT 1.0,
    language VARCHAR(10) DEFAULT 'en',
    timezone VARCHAR(50) DEFAULT 'UTC',
    notifications_enabled BOOLEAN DEFAULT TRUE,
    dnd_start TIME,
    dnd_end TIME,
    daily_briefing_time TIME DEFAULT '08:00:00',
    news_interests JSONB DEFAULT '[]',
    memory_auto_save BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Chats
CREATE TABLE chats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    mode VARCHAR(30) DEFAULT 'general',
    is_pinned BOOLEAN DEFAULT FALSE,
    is_archived BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_message_at TIMESTAMPTZ
);

-- Messages
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id UUID NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')),
    content TEXT NOT NULL,
    attachments JSONB DEFAULT '[]',
    model_used VARCHAR(50),
    tokens_input INTEGER,
    tokens_output INTEGER,
    latency_ms INTEGER,
    feedback VARCHAR(10) CHECK (feedback IN ('positive', 'negative')),
    parent_message_id UUID REFERENCES messages(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    edited_at TIMESTAMPTZ
);

-- Memories
CREATE TABLE memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category VARCHAR(30) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    source VARCHAR(20) DEFAULT 'auto' CHECK (source IN ('auto', 'manual', 'import')),
    source_chat_id UUID REFERENCES chats(id),
    confidence_score DECIMAL(3,2) DEFAULT 1.0,
    is_verified BOOLEAN DEFAULT FALSE,
    access_count INTEGER DEFAULT 0,
    embedding_id VARCHAR(255),
    tags TEXT[] DEFAULT '{}',
    last_accessed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Notes
CREATE TABLE notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    folder_id UUID REFERENCES note_folders(id) ON DELETE SET NULL,
    title VARCHAR(500),
    content TEXT,
    note_type VARCHAR(20) DEFAULT 'markdown' CHECK (note_type IN ('markdown', 'plain', 'rich', 'voice')),
    is_pinned BOOLEAN DEFAULT FALSE,
    is_starred BOOLEAN DEFAULT FALSE,
    audio_file_path TEXT,
    tags TEXT[] DEFAULT '{}',
    word_count INTEGER DEFAULT 0,
    embedding_id VARCHAR(255),
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Documents
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    folder_id UUID REFERENCES document_folders(id) ON DELETE SET NULL,
    filename VARCHAR(500) NOT NULL,
    display_name VARCHAR(500),
    format VARCHAR(10) NOT NULL,
    file_size_bytes BIGINT,
    storage_path TEXT NOT NULL,
    page_count INTEGER,
    word_count INTEGER,
    status VARCHAR(20) DEFAULT 'processing',
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    last_accessed_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tasks
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    parent_task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'todo',
    priority VARCHAR(10) DEFAULT 'medium',
    due_date TIMESTAMPTZ,
    reminder_at TIMESTAMPTZ,
    recurrence_rule TEXT,
    estimated_minutes INTEGER,
    actual_minutes INTEGER,
    tags TEXT[] DEFAULT '{}',
    created_by VARCHAR(10) DEFAULT 'user',
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agent Actions (audit log)
CREATE TABLE agent_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    session_id VARCHAR(255),
    tool_name VARCHAR(100) NOT NULL,
    tool_input JSONB,
    tool_output JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    required_confirmation BOOLEAN DEFAULT FALSE,
    confirmed_by_user BOOLEAN,
    execution_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Indexes

```sql
-- Performance indexes for common queries
CREATE INDEX idx_messages_chat_id ON messages(chat_id);
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX idx_chats_user_id ON chats(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_memories_user_id ON memories(user_id);
CREATE INDEX idx_notes_user_id ON notes(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_notes_fts ON notes USING gin(to_tsvector('english', coalesce(title,'') || ' ' || coalesce(content,'')));
CREATE INDEX idx_tasks_user_due ON tasks(user_id, due_date) WHERE status != 'done';
CREATE INDEX idx_documents_user_id ON documents(user_id) WHERE deleted_at IS NULL;
```

---

## 10. API Design

### Base URL Structure

```
/api/v1/{service}/{resource}
```

### Authentication

All endpoints require JWT Bearer token except `/auth/*`.

```
Authorization: Bearer <access_token>
```

### Service Endpoints Overview

#### Auth Service (`/api/v1/auth`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/auth/google` | Initiate Google OAuth |
| GET | `/auth/microsoft` | Initiate Microsoft OAuth |
| GET | `/auth/apple` | Initiate Apple OAuth |
| GET | `/auth/callback/{provider}` | OAuth callback handler |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/logout` | Revoke current session |
| GET | `/auth/sessions` | List active sessions |
| DELETE | `/auth/sessions/{session_id}` | Revoke specific session |

#### Chat Service (`/api/v1/chats`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/chats` | List all chats (paginated) |
| POST | `/chats` | Create new chat |
| GET | `/chats/{id}` | Get chat with messages |
| PATCH | `/chats/{id}` | Update title, pin, archive |
| DELETE | `/chats/{id}` | Soft-delete chat |
| POST | `/chats/{id}/messages` | Send message (triggers LLM) |
| GET | `/chats/{id}/messages` | Get messages (paginated) |
| DELETE | `/chats/{id}/messages/{msg_id}` | Delete message |
| POST | `/chats/{id}/messages/{msg_id}/feedback` | Submit feedback |
| POST | `/chats/{id}/export` | Export chat |
| WebSocket | `/ws/chats/{id}` | Stream LLM response |

#### Memory Service (`/api/v1/memories`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/memories` | List memories (filter by category) |
| POST | `/memories` | Create memory manually |
| GET | `/memories/{id}` | Get single memory |
| PATCH | `/memories/{id}` | Edit memory |
| DELETE | `/memories/{id}` | Delete memory |
| POST | `/memories/search` | Semantic memory search |
| POST | `/memories/{id}/verify` | Mark memory as verified |
| GET | `/memories/suggestions` | Get auto-extracted pending confirmations |

#### Voice Service (`/api/v1/voice`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/voice/transcribe` | Upload audio → get transcript |
| POST | `/voice/synthesize` | Text → audio (TTS) |
| WebSocket | `/ws/voice` | Bidirectional voice stream |
| GET | `/voice/voices` | List available TTS voices |

#### Agent Service (`/api/v1/agent`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/agent/execute` | Submit agentic task |
| GET | `/agent/status/{session_id}` | Poll execution status |
| POST | `/agent/confirm/{action_id}` | Confirm/deny pending action |
| GET | `/agent/history` | Agent action audit log |
| WebSocket | `/ws/agent/{session_id}` | Real-time agent progress stream |

### API Response Format

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 150
  },
  "error": null
}
```

### Error Format

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "MEMORY_NOT_FOUND",
    "message": "Memory with ID xyz does not exist",
    "details": {}
  }
}
```

### Rate Limiting

| Endpoint Group | Rate Limit |
|----------------|-----------|
| LLM Chat | 30 req/min per user |
| Voice Transcription | 20 req/min per user |
| Document Upload | 10 req/min per user |
| General API | 200 req/min per user |
| Auth Endpoints | 10 req/min per IP |

---

## 11. Vector Database Design

### Qdrant Collections

```
Collection: user_{user_id}_memories
  - Payload: { memory_id, category, title, content, tags, created_at }
  - Vector size: 768 (nomic-embed-text)
  - Distance: Cosine

Collection: user_{user_id}_notes
  - Payload: { note_id, title, chunk_index, content, folder, tags }
  - Vector size: 768
  - Distance: Cosine

Collection: user_{user_id}_documents
  - Payload: { document_id, filename, chunk_index, content, page_number }
  - Vector size: 768
  - Distance: Cosine

Collection: user_{user_id}_chats
  - Payload: { chat_id, message_id, role, content, created_at }
  - Vector size: 768
  - Distance: Cosine
```

### Retrieval Strategy

```python
# Context retrieval for chat
results = qdrant.search(
    collection_name=f"user_{user_id}_documents",
    query_vector=embed(user_query),
    limit=5,
    score_threshold=0.65,
    with_payload=True
)
# + cross-encoder reranking
# + metadata filter by document_id (if document-scoped chat)
```

---

## 12. Caching Strategy

### Redis Cache Layers

| Cache Key Pattern | Data | TTL |
|-------------------|------|-----|
| `user:{id}:profile` | User + preferences | 1 hour |
| `user:{id}:memories:summary` | Top-K memory summary string | 30 min |
| `chat:{id}:context` | Assembled context window | 15 min |
| `embed:{hash}` | Embedding vector for text | 24 hours |
| `llm:response:{hash}` | Cached identical LLM responses | 1 hour |
| `calendar:{user_id}:today` | Today's events | 15 min |
| `news:{user_id}:digest:{date}` | Daily news digest | 12 hours |
| `search:{user_id}:{query_hash}` | Web search results | 30 min |

### Cache Invalidation

- User profile cache: invalidated on any preference update
- Calendar cache: invalidated on any event create/edit/delete
- Memory summary: invalidated on memory CRUD
- Document chunks: invalidated on document re-processing

### Redis Pub/Sub Usage

- Real-time agent progress updates → `/ws/agent/{session_id}`
- Calendar sync completion notifications
- Document processing completion
- Memory extraction suggestions

---

## 13. LLM Gateway Architecture

### Provider Abstraction

```python
class BaseLLMProvider(ABC):
    async def complete(self, messages: list, config: LLMConfig) -> AsyncIterator[str]: ...
    async def embed(self, texts: list[str]) -> list[list[float]]: ...
    async def health_check(self) -> bool: ...

class OllamaProvider(BaseLLMProvider):
    # Handles: Qwen, Llama, Mistral, LLaVA, nomic-embed-text
    
class OpenAIProvider(BaseLLMProvider):
    # Future: GPT-4o, GPT-4-mini, text-embedding-3
    
class AnthropicProvider(BaseLLMProvider):
    # Future: Claude 3.5 Sonnet, Claude 3 Haiku
    
class GoogleProvider(BaseLLMProvider):
    # Future: Gemini 1.5 Pro, Gemini Flash

class LLMGateway:
    def __init__(self):
        self.providers = {
            "ollama/llama3.2": OllamaProvider("llama3.2"),
            "ollama/qwen2.5": OllamaProvider("qwen2.5"),
            "ollama/mistral": OllamaProvider("mistral"),
        }
    
    async def route(self, user_pref: str, fallback_chain: list) -> BaseLLMProvider:
        for model in [user_pref] + fallback_chain:
            provider = self.providers.get(model)
            if provider and await provider.health_check():
                return provider
        raise NoAvailableProviderError()
```

### Model Registry (Phase 1)

| Model ID | Provider | Use Case | Context Window |
|----------|----------|----------|----------------|
| `ollama/llama3.2` | Ollama | General chat, coding | 128K |
| `ollama/qwen2.5` | Ollama | Multilingual, reasoning | 128K |
| `ollama/mistral` | Ollama | Fast responses, summarization | 32K |
| `ollama/llava` | Ollama | Vision (image understanding) | 4K |
| `ollama/nomic-embed-text` | Ollama | Embeddings | N/A |

### Model Selection Logic

```
User Preference set? → Use that model
     ↓ No
Task type = vision? → Use llava
     ↓
Task type = code? → Use llama3.2 / qwen2.5
     ↓
Default → llama3.2 (most capable general)
     ↓
Model unavailable → fallback chain → error with user-friendly message
```

---

## 14. Security & Privacy

### Authentication Security

- JWT signed with RS256 (asymmetric keys, rotated monthly)
- Refresh tokens stored in HttpOnly Secure cookies (web) or secure keychain (mobile)
- PKCE flow for OAuth (prevents authorization code interception)
- CSRF protection on all state-changing endpoints
- Brute-force protection: 5 failed logins → 15-minute lockout

### Data Security

- All data encrypted at rest: PostgreSQL with pgcrypto extension for sensitive fields; AES-256 for file storage
- OAuth tokens (access + refresh) encrypted in DB using Fernet symmetric encryption
- TLS 1.2+ enforced on all connections
- Secrets never in code (environment variables + secrets manager)
- Database credentials rotated every 90 days
- No cross-user data access: all queries scoped by `user_id` with row-level security (PostgreSQL RLS)

### API Security

- Input validation on all endpoints (Pydantic v2 strict models)
- SQL injection prevention via ORM (no raw queries with user input)
- XSS prevention: all user content sanitized on output
- Content Security Policy headers
- CORS: explicit allowlist of frontend origins
- File upload: MIME type validation + antivirus scan (ClamAV) before processing
- Request signing for agent-initiated actions

### Privacy

- No telemetry sent to Anthropic or any third party
- All AI inference runs locally (Phase 1)
- User data never used for model training
- Minimal PII collection (only what's required)
- Privacy policy shown and accepted on first login
- Data retention settings: users control memory TTL, chat history retention

### Vulnerability Management

- Dependency scanning (Dependabot / pip-audit)
- OWASP Top 10 checklist applied during development
- Security review required before new auth or agent tool additions
- Agent command sandbox: separate restricted user process with read-only filesystem access by default

---

## 15. Non-Functional Requirements

### Performance

| Requirement | Target |
|------------|--------|
| API response time (non-LLM) | < 2 seconds P95 |
| LLM first token latency (local) | < 3 seconds P95 |
| Voice STT latency | < 2 seconds |
| Voice TTS audio start | < 1 second after LLM finishes |
| Search results | < 500ms |
| Dashboard load | < 1 second (cached) |
| Document upload + ingestion | < 60 seconds for 10MB PDF |
| Calendar sync | < 5 seconds for initial, < 1 second incremental |

### Scalability

| Dimension | Phase 1 Target | Phase 2 Target |
|-----------|----------------|----------------|
| Concurrent users | 1–10 (personal use) | 100–1,000 |
| Documents per user | 500 | 10,000 |
| Messages per chat | 1,000 | unlimited |
| Vector embeddings per user | 100,000 | 10,000,000 |
| LLM requests/day | 500 | 50,000 |

### Availability

- Target uptime: 99.0% during testing phase
- Graceful degradation: if local LLM is unavailable, user sees clear error with recovery steps
- Database connection pooling: PgBouncer (min 5, max 20 connections)
- Health check endpoints: `/health/live` and `/health/ready`
- Automatic restart on crash (Docker restart policy)

### Reliability

- All background jobs (Celery) have retry with exponential backoff (max 3 retries)
- Document ingestion failures don't affect other services
- Agent actions atomic: all-or-nothing for multi-step file operations
- Database migrations: Alembic with rollback capability

### Usability

- Mobile responsive: all features accessible on 375px screen width
- Keyboard navigation: all interactive elements reachable via keyboard
- Screen reader support: ARIA labels on all interactive elements
- Minimum tap target size: 44×44pt (iOS HIG / Material guidelines)
- Maximum 3 taps from any screen to any primary feature
- Empty states: helpful onboarding prompts on all empty views

### Accessibility

- WCAG 2.1 AA compliance for web
- Minimum contrast ratio 4.5:1
- Focus indicators visible
- Text scalable up to 200% without horizontal scrolling
- Voice-only navigation supported via voice assistant mode

### Localization

- Phase 1: English (US, IN)
- Phase 2: Hindi, German, Spanish, French, Japanese
- All strings externalized (ARB format for Flutter)
- RTL layout support architecture (ready for Arabic/Hebrew — Phase 3)

---

## 16. Phase 1 Scope

### In Scope (MVP)

- Google + Microsoft OAuth login
- Core AI chat with local Ollama models (Llama, Qwen, Mistral)
- Long-term memory system (auto + manual)
- Notes (Markdown + Plain Text)
- Document knowledge base (PDF, DOCX, TXT) with RAG
- Google Calendar + Microsoft Calendar integration
- Voice assistant (push-to-talk, Whisper + Piper)
- Basic web search (SearXNG)
- Personalized news digest (RSS-based)
- Phase 1 agent (file operations, URLs, commands)
- Task management with projects
- Dashboard with widgets
- Global search
- Smart notifications (in-app + push)
- Offline mode (view-only with sync queue)
- Data export (all formats)
- PostgreSQL + Redis + Qdrant + MinIO stack
- Flutter Web + Android app
- Docker Compose deployment

### Out of Scope (Phase 1)

- Apple OAuth / Apple Calendar
- iOS App (Flutter code is ready; distribution is Phase 2)
- Cloud LLM providers (GPT, Claude, Gemini)
- Real-time collaboration / sharing
- Third-party note imports (Notion, Obsidian)
- Email integration
- GitHub integration
- Mobile device LLM (on-device inference)
- Wake word activation
- End-to-end encryption (E2E)
- Multi-tenant / team features
- Billing / subscription management

---

## 17. Phased Roadmap

### Phase 1 — MVP (Months 1–4)

**Goal:** Fully functional personal use product

- [ ] Core infrastructure (Docker, PostgreSQL, Redis, Qdrant, MinIO)
- [ ] Authentication (Google + Microsoft OAuth, JWT)
- [ ] User profile + preferences
- [ ] LLM Gateway + Ollama integration
- [ ] Basic chat with streaming
- [ ] Memory system (auto + manual)
- [ ] Notes (markdown editor)
- [ ] Document upload + RAG pipeline
- [ ] Google Calendar integration
- [ ] Voice (push-to-talk, Whisper + Piper)
- [ ] Basic agent (file ops, URLs)
- [ ] Task management
- [ ] Dashboard
- [ ] Global search
- [ ] Flutter Web + Android app
- [ ] Push notifications

### Phase 2 — Enhanced Intelligence (Months 5–8)

- [ ] Apple OAuth + Apple Calendar
- [ ] iOS App store distribution
- [ ] Cloud LLM support (GPT-4o, Claude, Gemini)
- [ ] Advanced agent (email, calendar scheduling intelligence)
- [ ] Notion + Obsidian import
- [ ] Smart notifications + proactive suggestions
- [ ] Personal analytics dashboard
- [ ] Multimodal input (image understanding via LLaVA → cloud vision)
- [ ] Google Drive document import
- [ ] Continuous listening voice mode
- [ ] Advanced RAG (reranking, HyDE, multi-hop)

### Phase 3 — Scale & Collaboration (Months 9–12)

- [ ] End-to-end encryption option
- [ ] On-device LLM (mobile inference)
- [ ] Wake word activation
- [ ] GitHub integration (code context)
- [ ] Shared knowledge bases (team notes, docs)
- [ ] Calendar AI scheduling optimizer
- [ ] Health + habit tracking module
- [ ] Email integration (read + draft)
- [ ] Plugin/extension system for custom tools
- [ ] Self-hostable public release

### Phase 4 — Future Vision

- [ ] Microservices migration
- [ ] Federated learning for privacy-preserving personalization
- [ ] Autonomous agent workflows (multi-day tasks)
- [ ] API for third-party apps to integrate with the assistant
- [ ] AR/VR interface (spatial computing)

---

## 18. Open Questions & Risks

### Open Questions

| # | Question | Owner | Priority |
|---|---------|-------|----------|
| Q1 | Which Piper voice model should be default for Indian English users? | Voice Team | Medium |
| Q2 | Should memory extraction require explicit confirmation or be fully automatic with a "review" panel? | Product | High |
| Q3 | What is the acceptable storage quota per user for Phase 1? | Infra | Medium |
| Q4 | Should the agent have network access during command execution? | Security | High |
| Q5 | Should news digests use an external news API (NewsAPI) or rely purely on self-hosted SearXNG? | Product | Medium |
| Q6 | What is the minimum device spec for Flutter Android app? (RAM, Android version) | Mobile | Medium |
| Q7 | Should offline voice recording auto-transcribe on reconnect, or prompt user? | UX | Low |

### Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Local LLM quality gap vs GPT-4 | High | Medium | Frame local as privacy-first MVP; cloud LLMs in Phase 2 |
| Whisper latency too high on low-end devices | Medium | High | Offer whisper-small as low-latency option; server-side processing |
| OAuth token refresh failures causing user lockout | Low | High | Implement robust token refresh with fallback re-login |
| Qdrant collection isolation failure (cross-user data leak) | Very Low | Critical | Enforce `user_id` in every vector payload filter; automated test suite for isolation |
| Agent executing destructive commands unintentionally | Low | High | Hard confirmation gates; sandbox environment; audit log |
| Document ingestion pipeline bottleneck | Medium | Medium | Celery queue with auto-scaling workers; status polling for user |
| Flutter Web rendering performance on low-end browsers | Medium | Medium | Lazy loading, pagination; CanvasKit vs HTML renderer choice per device |
| Memory extraction hallucination (wrong facts saved) | Medium | Medium | Confidence threshold + user verification step; easy delete |

---

*End of Product Requirements Document*

*Version 1.0 — June 2026*  
*Next Review: Upon Phase 1 Sprint 1 Kickoff*
