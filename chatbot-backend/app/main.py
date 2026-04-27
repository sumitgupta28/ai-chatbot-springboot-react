import logging
import logging.config
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import dependencies
from app.config import settings
from app.routers import chat, documents, rag_chat

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        }
    },
    "loggers": {
        "app": {"level": "DEBUG", "handlers": ["console"], "propagate": False},
    },
    "root": {"level": "INFO", "handlers": ["console"]},
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=== Chatbot Backend starting up ===")
    logger.info("LLM provider : %s", settings.llm_provider)
    if settings.llm_provider == "anthropic":
        logger.info("Chat model   : %s", settings.anthropic_chat_model)
    else:
        logger.info("Chat model   : %s  (Ollama at %s)", settings.ollama_chat_model, settings.ollama_base_url)
    logger.info("Embedding    : %s", settings.embedding_model_name)

    logger.info("Initializing embedding model...")
    dependencies.init_embeddings()
    logger.info("Embedding model ready")

    logger.info("Initializing PGVector store...")
    dependencies.init_vector_store()
    logger.info("PGVector store ready")

    logger.info("Initializing sync database engine...")
    dependencies.init_sync_engine()
    logger.info("Sync engine ready")

    logger.info("Initializing LLM client...")
    dependencies.init_llm()
    logger.info("LLM client ready")

    logger.info("=== Startup complete — listening on port 8080 ===")
    yield
    logger.info("=== Chatbot Backend shutting down ===")


app = FastAPI(title="Chatbot Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(chat.router)
app.include_router(rag_chat.router)
app.include_router(documents.router)
