# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository layout

Three independently deployable services:

```
chatbot-backend/    # Python 3.11 · FastAPI · LangChain backend
chatbot-ui/         # React 18 frontend (Create React App)
docker-compose.yaml # Orchestrates all services (backend, frontend, PGVector)
Makefile            # Build and deploy shortcuts
```

## Backend — Python / FastAPI

All commands run from `chatbot-backend/`.

```bash
# Install dependencies
pip install -r requirements.txt

# Start PGVector first (see Docker Compose section below)
# Then run Alembic migrations
alembic upgrade head

# Start the dev server with hot-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

# Or use the Makefile shortcut (also starts PGVector)
make db        # from repo root — starts PGVector only
make migrate   # from repo root — runs Alembic migrations
make backend-dev  # from repo root — starts FastAPI with hot-reload
```

Listens on **port 8080**. Requires PostgreSQL (PGVector) on **port 5432** — start it via `make db` before running locally.

### Environment variables

Copy `.env.example` → `.env` inside `chatbot-backend/`. Key variables:

```dotenv
LLM_PROVIDER=ollama                   # "ollama" (default) or "anthropic"
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=llama3.2
ANTHROPIC_API_KEY=sk-ant-...          # required only when LLM_PROVIDER=anthropic
ANTHROPIC_CHAT_MODEL=claude-sonnet-4-6
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ragdb
DATABASE_SYNC_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/ragdb
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
```

Two database URLs are required:
- `DATABASE_URL` (asyncpg) — used by SQLAlchemy async ORM for `document_metadata` CRUD
- `DATABASE_SYNC_URL` (psycopg2) — used by LangChain PGVector and Alembic (both sync)

## Frontend — React

All commands run from `chatbot-ui/`.

```bash
npm start        # dev server on port 3000
npm test         # Jest / React Testing Library
npm run build    # production build
```

Or from repo root: `make frontend-dev`

## Docker Compose (full stack)

```bash
# Ollama (default) — Ollama must be running on the host at port 11434
make up

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-... make up-anthropic

# Start only PGVector (for local backend dev)
make db

# Rebuild everything from scratch
make rebuild

# Stop all services
make down

# Tail logs
make logs
```

All `make` targets are self-documented — run `make help` for the full list.

## AI model profiles

The active LLM provider is selected at startup via the `LLM_PROVIDER` environment variable.

| `LLM_PROVIDER` | Provider | Required env var |
|---|---|---|
| `ollama` *(default)* | Ollama (local) | none — Ollama at `http://localhost:11434` |
| `anthropic` | Anthropic Claude | `ANTHROPIC_API_KEY` |

Embeddings always use the local `all-MiniLM-L6-v2` model via `sentence-transformers` (384 dims, downloaded from HuggingFace on first use ~90 MB, cached afterwards). This is independent of the chat LLM provider.

## API endpoints

### Direct Chat (RAG-free) — `routers/chat.py`
- `GET /ai/chat/string` — SSE stream of text tokens; used by the **Chat** tab

### RAG Chat — `routers/rag_chat.py`
- `GET /rag/ai/chat/string/client` — RAG-augmented SSE stream; used by the **RAG Chat** tab

The RAG endpoint accepts per-request tuning parameters (all optional with defaults):

| Param | Default | Description |
|---|---|---|
| `message` | *(required)* | User query |
| `topK` | `5` | Max chunks retrieved from vector store |
| `similarityThreshold` | `0.0` | Min similarity score for a chunk to be included |
| `mode` | `soft` | `soft` = docs + general knowledge fallback; `strict` = docs only |
| `temperature` | `0.7` | LLM creativity (low = factual, high = creative) |
| `maxTokens` | `1000` | Caps response length |

### Documents — `routers/documents.py`
- `POST /documents/upload` — multipart file upload (PDF, TXT, DOCX); chunks, embeds, stores in PGVector
- `GET /documents` — list all indexed documents with metadata
- `DELETE /documents/{id}` — remove a document and its vectors from PGVector
- `GET /documents/verify` — vector store health: status, total chunk count, list of all indexed chunks
- `GET /documents/verify/search?query=&topK=&similarityThreshold=` — raw similarity search with scores; used by the **Vector Search** tab

### SSE streaming format

Both chat endpoints return `text/event-stream`. Each event:
```
data: <token>\n\n
```
End-of-stream marker:
```
data: [DONE]\n\n
```

## Frontend tabs

| Tab | Component | Backend endpoint |
|---|---|---|
| 💬 Chat | `ChatBot.js` | `GET /ai/chat/string` (SSE) |
| 🗄️ Vector Search | `VectorSearch.js` | `GET /documents/verify`, `GET /documents/verify/search` |
| 🔍 RAG Chat | `RAGChatbot.js` | `GET /rag/ai/chat/string/client` (SSE) |
| 📄 Documents | `DocumentUpload.js` | `GET /documents`, `POST /documents/upload`, `DELETE /documents/{id}` |

`ChatBot.js` and `RAGChatbot.js` use the browser's native `EventSource` API for SSE.
`DocumentUpload.js` and `VectorSearch.js` use axios (non-streaming).

## Key architecture notes

- **Two URL databases**: `DATABASE_URL` uses `asyncpg` for async SQLAlchemy ORM. `DATABASE_SYNC_URL` uses `psycopg2` for LangChain PGVector (which is synchronous). Never swap them. All PGVector calls are offloaded to a thread pool via `anyio.to_thread.run_sync()` to avoid blocking the async event loop.
- **Singletons in `dependencies.py`**: `HuggingFaceEmbeddings`, `PGVector`, and the base LLM are initialized once during FastAPI `lifespan` startup and injected via `Depends()`. Per-request temperature/maxTokens create a fresh LLM instance via `create_llm()` — inexpensive since these are thin HTTP clients.
- **RAG modes**: `soft` — uses document context if found, falls back to general knowledge if no chunks match. `strict` — returns a short-circuit message without calling the LLM if no chunks match.
- **Similarity score**: `similarity_search_with_score()` returns cosine *distance* (0 = identical). Convert to similarity: `similarity = 1.0 - distance`. Always apply this conversion before filtering against `similarityThreshold` or returning to the client.
- **Document deletion**: Vectors are deleted from `langchain_pg_embedding` via raw SQL filtered on `cmetadata->>'filename'`, then the `document_metadata` row is deleted. Both happen in a single logical unit.
- **Chunking**: `RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=100)`. Chunks shorter than 50 characters are discarded. Each chunk carries `metadata["filename"]` for filtering and deletion.
- **CORS**: Configured in `app/main.py` — currently allows `http://localhost:3000`. Update `allow_origins` if the frontend URL changes.
- **Alembic**: Manages only the `document_metadata` table. LangChain PGVector (`langchain_pg_collection`, `langchain_pg_embedding`) creates its own tables at startup. Do not include LangChain tables in Alembic migrations.

## Database schema

### `document_metadata` (Alembic-managed)

| Column | Type | Notes |
|---|---|---|
| `id` | BIGSERIAL PK | Auto-increment |
| `filename` | VARCHAR(255) | Original file name |
| `content_type` | VARCHAR(100) | MIME type |
| `file_size` | BIGINT | Bytes |
| `upload_time` | TIMESTAMP | `server_default=NOW()` |
| `chunk_count` | INTEGER | Chunks created from this document |

### LangChain vector store (auto-created at startup)

| Table | Purpose |
|---|---|
| `langchain_pg_collection` | Named collection — `collection_name="chatbot_documents"` |
| `langchain_pg_embedding` | Vectors with `cmetadata` JSONB (includes `filename`), HNSW index |

## Package structure

```
chatbot-backend/
├── app/
│   ├── main.py                  # FastAPI app, CORS middleware, lifespan, router wiring
│   ├── config.py                # pydantic-settings — all env vars loaded here
│   ├── dependencies.py          # singletons: embeddings, vector_store, llm, sync_engine
│   ├── routers/
│   │   ├── chat.py              # GET /ai/chat/string
│   │   ├── rag_chat.py          # GET /rag/ai/chat/string/client
│   │   └── documents.py         # /documents/* (upload, list, delete, verify, search)
│   ├── services/
│   │   ├── rag_service.py       # build_rag_context(), verify_vector_store(), search_documents()
│   │   └── ingestion_service.py # ingest_document(), list_documents(), delete_document()
│   ├── models/
│   │   ├── db.py                # SQLAlchemy DocumentMetadata ORM model
│   │   └── schemas.py           # Pydantic response schemas (DocumentInfo, SearchResult, etc.)
│   ├── db/
│   │   └── session.py           # async SQLAlchemy engine + get_db() FastAPI dependency
│   └── parsers/
│       ├── pdf_parser.py        # PyMuPDF — extract_text_from_pdf(bytes) -> str
│       ├── docx_parser.py       # python-docx — extract_text_from_docx(bytes) -> str
│       └── txt_parser.py        # built-in — extract_text_from_txt(bytes) -> str
├── alembic/
│   └── versions/
│       └── 0001_init_document_metadata.py
├── alembic.ini
├── .env                         # local dev config (not committed)
├── .env.example                 # template
├── requirements.txt
└── Dockerfile
```

## RAG configuration defaults

Fallback values when no per-request params are supplied, defined in `config.py` and `.env`:

```dotenv
RAG_MODE=soft
RAG_TOP_K=5
RAG_SIMILARITY_THRESHOLD=0.0
```
