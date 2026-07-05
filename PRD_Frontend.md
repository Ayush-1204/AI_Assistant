# Frontend Product Requirements Document (PRD) 
# Personal AI Assistant Platform — "Second Brain"

**Version:** 1.0  
**Status:** Draft  
**Target Clients:** Web, Android, iOS (via Flutter)

---

## 1. Executive Summary

This document defines the frontend product requirements for the "Second Brain" Personal AI Assistant Platform. While the backend handles intelligent agent execution, memory management, and embeddings, the frontend provides a unified, cross-platform UI/UX that blends natural conversation with rich productivity tools (Tasks, Notes, Calendar, Documents). 

The goal of the frontend is to provide a seamless, low-latency, and fluid user experience that feels like a native OS capability rather than just a chat window. 

---

## 2. Platform & Technology Stack

To ensure a single codebase across Web, Android, and iOS while maintaining high performance, the frontend utilizes **Flutter**.

| Category | Technology | Rationale |
|----------|------------|-----------|
| **Framework** | Flutter (Dart) | Single codebase for Web, Android, iOS with near-native performance. |
| **State Management** | Riverpod | Scalable, compile-safe, and reactive state management. |
| **Local Storage** | Isar / Hive | Fast offline-first data persistence for caching and local configs. |
| **Networking** | `dio` + `web_socket_channel` | Robust HTTP client for REST APIs and WebSocket for streaming. |
| **Audio Processing** | `flutter_sound` / `record` | High-quality audio capture for Voice activity and local playback. |
| **Rich Text Rendering** | `flutter_markdown` | Support for GFM, code syntax highlighting, and LaTeX (via plugins) for LLM output. |

---

## 3. UI/UX Architecture & Layouts

### 3.1 Global Navigation
- **Sidebar (Web/Desktop) / Bottom Nav (Mobile):** 
  - Chat/Agent Interface (Default)
  - Notes & Knowledge Base
  - Calendar & Tasks
  - Documents & Files
  - Settings & Memory Management

### 3.2 Core Views
#### A. The Intelligent Chat View
The core interface where users interact with the assistant.
- **Message Feed:** Displays text, markdown, code blocks, and rich widgets (e.g., interactive calendar cards if the AI schedules a meeting).
- **Input Area:** Text field, attachment button (documents/images), and a prominent **Voice Recording (Push-to-talk)** button.
- **Context Indicators:** Visual tags indicating if the assistant is searching the Web, looking at uploaded Documents (RAG), or checking Calendar.

#### B. Notes & Knowledge View
- **List / Grid Layout:** View all synced notes.
- **Rich Editor:** Markdown editor with live preview for plain text, or WYSIWYG capabilities. 
- **AI Commands:** Floating action button in the editor for inline AI processing (e.g., `/summarize`, `/expand`).

#### C. Documents & RAG Manager 
- **Upload Interface:** Drag-and-drop zone (Web) or file picker (Mobile) for PDFs, DOCX, TXT.
- **Document List:** Shows processing status (Uploading -> Extracting -> Embedding -> Ready).
- **Document Preview:** Simple viewer with options to initiate a "Chat with this document".

#### D. Calendar & Task View
- **Daily/Weekly Agenda:** Read-only view synced with backend's calendar data.
- **Task List:** Kanban or list view of generated tasks.

#### E. Memory & Profile Manager
- **Memory Cards:** UI displaying auto-extracted memories categorized by (Facts, Preferences, Projects).
- **Verification UI:** Prompt users to confirm or reject newly detected memories.

---

## 4. Key Functional Requirements

### 4.1 Authentication Flow
- OAuth 2.0 login integration (Google, Apple, Microsoft) via native web-views or auth plugins.
- Secure storage of JWT tokens (Access & Refresh) using `flutter_secure_storage`.
- Automatic token refresh interception in network requests.

### 4.2 Real-time Chat & Streaming
- **SSE (Server-Sent Events) Handling:** Process incoming token chunks from the backend and update the UI incrementally to simulate typing.
- **Optimistic UI:** When a user sends a message, immediately display it locally before backend confirmation.
- **Citations & Grounding:** Support structured JSON citations (e.g., `[Source: Doc.pdf]`) and render them as clickable inline tooltip elements.

### 4.3 Voice & Audio Pipeline
- **Continuous Listening / Push-to-Talk:** Utilize microphone streams.
- **Audio Streaming:** Stream raw audio bytes over WebSockets to the backend `StreamingCoordinator` for instant processing.
- **Barge-in (Interruption) Support:** Immediately halt TTS playback if the user presses the microphone button or if client-side VAD (Voice Activity Detection) detects speech.

### 4.4 Offline Gracefulness & Caching
- Cache conversation history locally. If offline, the user can read existing notes and chats.
- Prevent interactions that require backend LLMs when offline, displaying a clear "Offline Mode" banner.
- Queue actions (e.g., note edits) locally and sync them upon network reconnection.

### 4.5 Theming & Responsiveness
- **Dark / Light Mode:** Native support reacting to system preferences.
- **Responsive Breakpoints:** 
  - Mobile (< 600px): Navigation moves to bottom or hamburger menu.
  - Tablet/Desktop (> 600px): Expandable left sidebar. Multi-pane layouts (e.g., Document list on left, Document Chat on right).

---

## 5. Integration with Backend APIs

The frontend will consume the FastAPI backend defined in the global architecture.
- **REST Endpoints:** Authentication (`/auth`), Notes CRUD (`/notes`), Document upload (`/documents`), Tasks (`/tasks`), Memory (`/memory`).
- **SSE Endpoints:** Text-based AI chat streaming (`/chat/stream`).
- **WebSocket Endpoints:** Bidirectional Voice endpoints (`/voice/{conversation_id}`).

---

## 6. Performance & UX Metrics

- **Time to Interactive (TTI):** App must load and be ready for interaction within < 1.5 seconds.
- **Frame Rate:** Sustain 60 FPS (or 120 FPS on supported devices) during scrolling and chat rendering.
- **Markdown Rendering Latency:** Ensure long markdown threads with code blocks do not cause UI thread jank. Implement lazy rendering / virtualization for large chat histories.
- **Voice Feedback:** Visual indicator (waveform or pulsating orb) must react to local mic input within 50ms to ensure the user knows they are being recorded.

---

## 7. Phase 1 Release Scope (Frontend)
1. Flutter App scaffolding with Riverpod setup.
2. OAuth Login Screens and JWT management.
3. Chat Interface supporting SSE Markdown streaming.
4. Voice input button streaming local audio to the WebSocket backend.
5. Simple Notes lists and Document upload UI.
6. Settings view to manage user Profile.
