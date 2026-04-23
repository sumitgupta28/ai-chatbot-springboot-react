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

`ChatController` is provider-agnostic. Embeddings always use the local ONNX model (`all-MiniLM-L6-v2` via `spring-ai-transformers`) regardless of which chat profile is active — no Ollama or external API needed for embeddings.

When adding a new provider, add its `spring-ai-starter-model-*` dependency to `build.gradle`, create an `application-<profile>.yaml` with `spring.ai.model.chat: <provider>`, and activate it via `--spring.profiles.active=<profile>`.

## API endpoints

### Chat
Both endpoints accept `?message=<text>`. Before calling the LLM they perform a PGVector similarity search and inject relevant document context as a system prompt (RAG).

- `GET /ai/chat` — streams full `ChatResponse` objects (JSON)
- `GET /ai/chat/string` — streams plain text tokens

### Documents (RAG ingestion)
- `POST /documents/upload` — multipart file upload (PDF, TXT, DOCX); chunks, embeds, and stores in PGVector
- `GET /documents` — list all indexed documents with metadata
- `DELETE /documents/{id}` — remove a document and its vectors from PGVector

The React frontend calls `/ai/chat/string` and `/documents/*` via axios. CORS is restricted to `http://localhost:3000`.

## RAG configuration

Controlled entirely via `application.yaml` — no code changes needed to switch modes:

```yaml
app:
  rag:
    mode: soft          # 'soft' = use docs when relevant, fall back to general knowledge
                        # 'strict' = answer only from docs; canned reply if no context found
    top-k: 5            # number of document chunks retrieved per query
    similarity-threshold: 0.7
```

## Key architecture notes

- `ChatController` calls `RagService.buildRagContext()` before every LLM call. It injects a `SystemMessage` with retrieved chunks when context is found; falls back to plain `UserMessage` when the vector store has no relevant hits (soft mode) or short-circuits with a canned reply (strict mode).
- `EmbeddingConfig` defines `TransformersEmbeddingModel` as `@Primary`, which prevents `OllamaEmbeddingModel` from being auto-configured. The ONNX model (`all-MiniLM-L6-v2`, 384 dims) is downloaded from HuggingFace on first use (~90 MB); subsequent starts use the cached copy.
- `IngestionService` uses `TikaDocumentReader` (Apache Tika — handles PDF, DOCX, TXT) → `TokenTextSplitter` → `VectorStore`. Document metadata is also persisted to the `document_metadata` table in PostgreSQL.
- Deletion removes rows from both `vector_store` (filtered by `metadata->>'filename'`) and `document_metadata`.
- `WebConfig` is the only CORS configuration; update `allowedOrigins` if the frontend URL changes.
- The React app makes a **single non-streaming GET request** via axios (it waits for the full response). Switching to true SSE streaming would require changing `Chatbot.js` to use `EventSource` or `fetch` with a `ReadableStream`.
- Docker Compose passes `SPRING_AI_OLLAMA_BASE_URL` to override the Ollama URL inside containers (`host.docker.internal:11434` by default). PGVector datasource URL is also overridden via `SPRING_DATASOURCE_URL=jdbc:postgresql://pgvector:5432/ragdb`.
- All Java classes use Lombok `@Slf4j` for logging.

## Package structure

```
in.ai.chatbot.config
├── config/
│   ├── WebConfig.java          # CORS
│   ├── EmbeddingConfig.java    # TransformersEmbeddingModel bean (@Primary)
│   └── RagProperties.java      # @ConfigurationProperties for app.rag.*
├── controller/
│   ├── ChatController.java     # /ai/chat and /ai/chat/string
│   └── DocumentController.java # /documents/*
├── model/
│   └── DocumentInfo.java       # record returned by document endpoints
└── service/
    ├── RagService.java         # similarity search + prompt augmentation
    └── IngestionService.java   # document parsing, chunking, vector storage
```
