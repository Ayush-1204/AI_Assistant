from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Second Brain API"
    APP_VERSION: str = "0.1.0"

    DEBUG: bool = True

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str

    # File Storage
    UPLOAD_DIR: str = "storage/uploads"

    # 50 MB
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024

    ALLOWED_DOCUMENT_TYPES: list[str] = [
        "application/pdf",
        "text/plain",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/markdown",
    ]

    # -------------------------
    # RAG Configuration
    # -------------------------

    rag_chunk_size: int = 512
    rag_chunk_overlap: int = 64
    rag_top_k: int = 5
    rag_similarity_threshold: float = 0.35
    max_document_chunks: int = 5
    max_memory_items: int = 10
    max_history_messages: int = 20
    retrieval_allow_best_match_fallback: bool = True

    max_context_tokens: int = 16000
    max_tool_results: int = 5
    max_tool_output_length: int = 2000
    reserved_response_tokens: int = 2000

    # Hybrid Retrieval
    enable_hybrid_retrieval: bool = True
    enable_reranking: bool = False
    dense_top_k: int = 5
    keyword_top_k: int = 5
    reranker_candidate_count: int = 10
    reranker_output_count: int = 5

    # Routing
    default_provider: str = "gemini"
    default_model: str = "gemini-2.5-flash"
    fallback_provider_chain: list[str] = ["gemini", "ollama"]
    retry_count: int = 3
    retry_backoff: float = 2.0
    health_check_interval: int = 60
    routing_strategy: str = "priority"
    load_balancing_strategy: str | None = None

    # Agent Planning
    MAX_AGENT_STEPS: int = 10
    ENABLE_MULTI_STEP_AGENT: bool = True
    ENABLE_TOOL_RESULT_CACHE: bool = True
    MAX_TOOL_RETRIES_PER_STEP: int = 3

    # Web Search
    enable_web_search: bool = True
    default_search_provider: str = "tavily"
    default_max_results: int = 5
    search_timeout: int = 15
    TAVILY_API_KEY: str | None = None

    # JWT
    SECRET_KEY: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Gemini
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.5-flash"
    
    # Fast Models
    GROQ_API_KEY: str | None = None
    OPENROUTER_API_KEY: str | None = None

    # Google Workspace
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GOOGLE_REDIRECT_URI: str | None = None

    # Scheduler & Notifications
    ENABLE_SCHEDULER: bool = True
    ENABLE_EMAIL_NOTIFICATIONS: bool = False
    ENABLE_PUSH_NOTIFICATIONS: bool = False
    SCHEDULER_INTERVAL_SECONDS: int = 10
    MAX_JOB_RETRIES: int = 3
    JOB_TIMEOUT_SECONDS: int = 600
    FIREBASE_CREDENTIALS_PATH: str = ""

    # Voice Configuration
    ENABLE_VOICE: bool = True
    DEFAULT_STT_PROVIDER: str = "whisper"
    DEFAULT_TTS_PROVIDER: str = "deepgram"
    MAX_AUDIO_DURATION: int = 60
    STREAMING_CHUNK_MS: int = 100
    
    DEEPGRAM_API_KEY: str | None = None
    ELEVENLABS_API_KEY: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()