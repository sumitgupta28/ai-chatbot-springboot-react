import logging

from langchain_anthropic import ChatAnthropic
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_postgres import PGVector
from sqlalchemy import create_engine

from app.config import settings

logger = logging.getLogger(__name__)

_embeddings: HuggingFaceEmbeddings | None = None
_vector_store: PGVector | None = None
_llm = None
_sync_engine = None


def init_embeddings() -> None:
    global _embeddings
    logger.debug("Loading HuggingFace embeddings: model=%s", settings.embedding_model_name)
    _embeddings = HuggingFaceEmbeddings(
        model_name=settings.embedding_model_name,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    logger.debug("HuggingFace embeddings loaded (384-dim, normalize=True)")


def init_vector_store() -> None:
    global _vector_store
    logger.debug("Creating PGVector store (collection=chatbot_documents)")
    _vector_store = PGVector(
        embeddings=_embeddings,
        collection_name="chatbot_documents",
        connection=settings.database_sync_url,
        use_jsonb=True,
    )
    logger.debug("PGVector store created")


def init_sync_engine() -> None:
    global _sync_engine
    logger.debug("Creating sync SQLAlchemy engine")
    _sync_engine = create_engine(settings.database_sync_url, pool_pre_ping=True)
    logger.debug("Sync engine created")


def init_llm() -> None:
    global _llm
    _llm = create_llm()
    if settings.llm_provider == "anthropic":
        logger.debug("Base LLM: ChatAnthropic model=%s", settings.anthropic_chat_model)
    else:
        logger.debug("Base LLM: ChatOllama model=%s base_url=%s", settings.ollama_chat_model, settings.ollama_base_url)


def get_embeddings() -> HuggingFaceEmbeddings:
    return _embeddings


def get_vector_store() -> PGVector:
    return _vector_store


def get_llm():
    return _llm


def get_sync_engine():
    return _sync_engine


def create_llm(temperature: float = 0.7, max_tokens: int = 1000):
    if settings.llm_provider == "anthropic":
        logger.debug(
            "Creating ChatAnthropic: model=%s temperature=%s max_tokens=%d",
            settings.anthropic_chat_model, temperature, max_tokens,
        )
        return ChatAnthropic(
            model=settings.anthropic_chat_model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=settings.anthropic_api_key,
        )
    logger.debug(
        "Creating ChatOllama: model=%s temperature=%s num_predict=%d",
        settings.ollama_chat_model, temperature, max_tokens,
    )
    return ChatOllama(
        model=settings.ollama_chat_model,
        temperature=temperature,
        num_predict=max_tokens,
        base_url=settings.ollama_base_url,
    )
