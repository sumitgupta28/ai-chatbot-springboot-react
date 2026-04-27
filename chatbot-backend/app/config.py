from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    llm_provider: str = "ollama"

    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "llama3.2"

    anthropic_api_key: str = ""
    anthropic_chat_model: str = "claude-sonnet-4-6"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ragdb"
    database_sync_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/ragdb"

    rag_mode: str = "soft"
    rag_top_k: int = 5
    rag_similarity_threshold: float = 0.0

    embedding_model_name: str = "all-MiniLM-L6-v2"
    max_upload_size_mb: int = 50


settings = Settings()
