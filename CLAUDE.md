# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository layout

Two independently deployable services:

```
spring-boot-ai-chatbot/   # Spring Boot 3.5 + Spring AI 1.1.4 backend
chatbot-ui/               # React 18 frontend (Create React App)
docker-compose.yaml       # Orchestrates all services (backend, frontend, PGVector)
```

## Backend — Spring Boot

All commands run from `spring-boot-ai-chatbot/`.

```bash
./gradlew bootRun                                             # default profile (Ollama)
ANTHROPIC_API_KEY=sk-... ./gradlew bootRun --args='--spring.profiles.active=anthropic'
./gradlew test                                               # run all tests
./gradlew test --tests "in.ai.chatbot.config.SomeTest"       # run a single test class
./gradlew bootJar                                            # build the fat JAR
```

Listens on **port 8080**. Requires PostgreSQL (PGVector) on **port 5432** — start it via Docker Compose before running locally.

## Frontend — React

All commands run from `chatbot-ui/`.

```bash
npm start    # dev server on port 3000
npm test     # Jest/React Testing Library
npm run build
```

## Docker Compose (full stack)

```bash
# Ollama default (Ollama must be running on the host at port 11434)
docker compose up --build

# Anthropic profile
SPRING_PROFILES_ACTIVE=anthropic ANTHROPIC_API_KEY=sk-ant-... docker compose up --build

# Start only PGVector (for local backend dev)
docker compose up pgvector -d
```

Copy `.env.example` → `.env` for environment variables.

## AI model profiles

The backend uses **Spring AI's `ChatModel` interface** — the active provider is selected via `spring.ai.model.chat` in config.

| Profile | Provider | Config file | Required env var |
|---|---|---|---|
| *(default)* | Ollama (local) | `application.yaml` | none — Ollama at `http://localhost:11434` |
| `anthropic` | Anthropic Claude | `application-anthropic.yaml` | `ANTHROPIC_API_KEY` |

Embeddings always use the local ONNX model (`all-MiniLM-L6-v2` via `spring-ai-transformers`) regardless of which chat profile is active.

When adding a new provider, add its `spring-ai-starter-model-*` dependency to `build.gradle`, create an `application-<profile>.yaml` with `spring.ai.model.chat: <provider>`, and activate it via `--spring.profiles.active=<profile>`.

## API endpoints

### Direct Chat (RAG-free) — `ChatController`
- `GET /ai/chat` — streams full `ChatResponse` objects (JSON), not used by frontend
- `GET /ai/chat/string` — streams plain text tokens; used by the **Chat** tab

### RAG Chat — `RagChatController`
- `GET /rag/ai/chat` — RAG-augmented `ChatResponse` stream, not used by frontend
- `GET /rag/ai/chat/string` — RAG plain-text stream, not used by frontend
- `GET /rag/ai/chat/string/client` — **active endpoint** used by the **RAG Chat** tab

The active RAG endpoint accepts per-request tuning parameters (all optional with defaults):

| Param | Default | Description |
|---|---|---|
| `message` | *(required)* | User query |
| `topK` | `5` | Max chunks retrieved from vector store |
| `similarityThreshold` | `0.0` | Min similarity score for a chunk to be included |
| `mode` | `soft` | `soft` = docs + general knowledge fallback; `strict` = docs only |
| `temperature` | `0.7` | LLM creativity (low = factual, high = creative) |
| `maxTokens` | `1000` | Caps response length |

### Documents — `DocumentController`
- `POST /documents/upload` — multipart file upload (PDF, TXT, DOCX); chunks, embeds, and stores in PGVector
- `GET /documents` — list all indexed documents with metadata
- `DELETE /documents/{id}` — remove a document and its vectors from PGVector
- `GET /documents/verify` — returns vector store health: status, total chunk count, and a list of all indexed chunks with filename, size, and content preview
- `GET /documents/verify/search?query=&topK=&similarityThreshold=` — runs a raw similarity search and returns matched chunks with filename, similarity score, and content preview; used by the **Vector Search** tab

## Frontend tabs

| Tab | Component | Backend endpoint |
|---|---|---|
| 💬 Chat | `ChatBot.js` | `GET /ai/chat/string` |
| 🗄️ Vector Search | `VectorSearch.js` | `GET /documents/verify`, `GET /documents/verify/search` |
| 🔍 RAG Chat | `RAGChatbot.js` | `GET /rag/ai/chat/string/client` |
| 📄 Documents | `DocumentUpload.js` | `GET /documents`, `POST /documents/upload`, `DELETE /documents/{id}` |

## Key architecture notes

- **Two chat controllers**: `ChatController` calls the LLM directly with no document context. `RagChatController` calls `RagService.buildRagContext()` first to inject relevant document chunks as a system prompt before every LLM call.
- `RagService.buildRagContext(message, topK, similarityThreshold, mode)` performs a PGVector similarity search and builds the system prompt. The no-arg overload delegates to this using values from `RagProperties`.
- `RagService.searchDocuments(query, topK, threshold)` is the raw search used by the Vector Search tab — returns matched chunks with similarity scores computed as `1 - distance`.
- `EmbeddingConfig` defines `TransformersEmbeddingModel` as `@Primary`, which prevents `OllamaEmbeddingModel` from being auto-configured. The ONNX model (`all-MiniLM-L6-v2`, 384 dims) is downloaded from HuggingFace on first use (~90 MB); subsequent starts use the cached copy.
- `IngestionService` uses `TikaDocumentReader` (Apache Tika — handles PDF, DOCX, TXT) → `TokenTextSplitter` → `VectorStore`. Document metadata is also persisted to the `document_metadata` table in PostgreSQL.
- Deletion removes rows from both `vector_store` (filtered by `metadata->>'filename'`) and `document_metadata`.
- `WebConfig` is the only CORS configuration; update `allowedOrigins` if the frontend URL changes (currently restricted to `http://localhost:3000`).
- The React app makes a **single non-streaming GET request** via axios. Switching to true SSE streaming would require `EventSource` or `fetch` with a `ReadableStream` in the chat components.
- All Java classes use Lombok `@Slf4j` for logging.

## RAG configuration defaults

Fallback values when no per-request params are supplied, defined in `RagProperties` and `application.yaml`:

```yaml
app:
  rag:
    mode: soft
    top-k: 5
    similarity-threshold: 0.0
```

## Package structure

```
in.ai.chatbot.config
├── config/
│   ├── WebConfig.java              # CORS
│   ├── EmbeddingConfig.java        # TransformersEmbeddingModel bean (@Primary)
│   └── RagProperties.java          # @ConfigurationProperties for app.rag.*
├── controller/
│   ├── ChatController.java         # /ai/chat and /ai/chat/string (RAG-free)
│   ├── RagChatController.java      # /rag/ai/chat/* (RAG-augmented, active: /string/client)
│   └── DocumentController.java     # /documents/* including /verify and /verify/search
├── model/
│   └── DocumentInfo.java           # record returned by document list endpoint
└── service/
    ├── RagService.java             # similarity search, prompt augmentation, vector store queries
    └── IngestionService.java       # document parsing, chunking, vector storage
```
