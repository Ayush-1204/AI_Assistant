<div align="center">
  <img alt="Project Zenith" src="https://via.placeholder.com/400x150/000000/FFFFFF?text=ZENITH+AI" width="400">

  <p><i>The Omnipresent Local-First Assistant.</i></p>

  <p>
    <img src="https://img.shields.io/badge/project-Zenith-blue" alt="Project">
    <img src="https://img.shields.io/badge/python-%3E%3D3.12-blue" alt="Python">
    <img src="https://img.shields.io/badge/flutter-Web%20%7C%20iOS%20%7C%20Android-cyan" alt="Flutter">
    <img src="https://img.shields.io/badge/database-PostgreSQL%20%7C%20Qdrant-orange" alt="Tech">
    <a href="#"><img src="https://img.shields.io/badge/license-Apache%202.0-green" alt="License"></a>
  </p>
</div>

---

> **Personal AI, unified across endpoints.**
> Zenith bridges the gap between cloud-reliant wrappers and inflexible local LLMs by dynamically orchestrating compute where it belongs. Featuring real-time Voice Streaming with **Fast Brain zero-latency Audio presence**, automated Daily Schedulers, and RAG contextual execution engines.

## Why This Architecture?

Existing consumer AI assistants force users entirely onto the cloud. We built this ecosystem utilizing **Domain-Driven Design (DDD)** on FastAPI alongside a fully modular Flutter multi-platform toolkit to ensure that tools, documents, context, and integrations run natively local-first. We actively implement optimized routing heuristics:

- **Fast Brain / Slow Brain Presence:** While deep Vector-DB searches block thread execution, ultra-low-latency `EdgeTTS` injections run asynchronously to drop `Time-To-First-Audio (TTFA)` drastically for realistic human-like voice conversations.
- **Unified Proactive Engine:** Native integration with Celery Daemon Schedulers. The system doesn't just wait for questions—it autonomously executes timed behaviors and emits push/email notifications.
- **Provider Agnostic Tool Calling:** Dynamic API binding over standard and non-standard native models (`gemini-2.5-flash-native`, `OllamaLlama3`, `Groq`).

## Tech Stack Overview

| Domain | Tech | Responsibilities |
|---|---|---|
| **Frontend Runtime** | **Flutter (Web/Mobile)** | Cross-platform glassmorphism UI, WebSockets Audio Processing, 16kHz DSP noise-suppressed capturing |
| **Backend API** | **FastAPI (Python 3.12)** | Asynchronous endpoints, WebSockets controllers, Auth routing |
| **Memory / Graph** | **PostgreSQL & Qdrant** | Full-text relational state tracking combined with Dense Semantic vectors |
| **Generative Brain** | **LangChain & ProviderRouter** | Fallback-capable Exponential Backoffs for Gemini, OpenAI, Groq, local Ollama |
| **Task Queue** | **Celery & Redis** | Persistent cron-job schedulers for proactive behavior routines |

## Quick Start
*Boot the ecosystem locally:*

### Backend Bootstrapping
```bash
cd apps/api
# Create and source environment
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Start DBs locally
docker-compose up -d

# Start the unified backend
uvicorn app.main:app --reload
```
### Native Proactive Monitors
If you wish to arm the background task loop (Cron capabilities):
```bash
# In a secondary terminal
cd apps/api && source venv/bin/activate
celery -A app.services.scheduler.worker worker --loglevel=info
```

### Dashboard GUI
```bash
cd apps/client/web
flutter pub get
# Fire up the Glassmorphism realtime UI
flutter run -d chrome
```

## Advanced Operations

### 1. Zero-Latency Voice Mode
The application exposes a native Voice WebSockets pipe bridging Flutter to FastAPI over WebRTC-style async blobs. When invoking commands, the **Fast Brain** kicks in:

*User: "Check my email for flight updates."*  
*Fast Brain injected output (~200ms): "Hmm, pulling those up..."*  
*(Slow Brain parses Gmail integrations via the `ContextBuilder` taking 3 seconds in the background).*

### 2. Live Proactive Dashboard
We explicitly implemented `gemini-2.5-flash-lite` provider binding using strict `intent="dashboard"` routing chains to ensure widgets like Weather, Tasks, and Metrics update live in parallel using fallback exponent retries.

### 3. Integrated Agents and Skills
Simply install or structure new integrations dynamically in `apps/api/app/services/ai/tools`.
Current capabilities:
- **Tavily Web Search** [Native API]
- **Google Calendar/OAuth** [Native API]
- **Proactive Planners & Dispatchers** [Database-backed]
- **Interactive Markdown Collages** [Flutter Custom Syntax Renderer w/ Lightbox Gallery]
- **Universal Memory Extractors** [RAG Ingestion for TXT/MD/JSON/PDF]

---

<div align="center">
  <p><b>Built for the future of Sovereign Intelligence.</b></p>
</div>
