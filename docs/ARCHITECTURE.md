                        Android
                           │
                        Web App
                           │
──────────────────────── API Layer ────────────────────────
                           │
                        FastAPI
                           │
──────────────────── Service Layer ────────────────────────
│
├── AuthService
├── UserService
├── ConversationService
├── MessageService
└── AIService
        │
        ├── ContextBuilder
        ├── PromptBuilder
        ├── Memory (future)
        ├── RAG (future)
        └── Tool Manager (future)
                           │
──────────────── Repository Layer ─────────────────────────
│
├── UserRepository
├── ConversationRepository
└── MessageRepository
                           │
──────────────── Database ─────────────────────────────────
                     PostgreSQL