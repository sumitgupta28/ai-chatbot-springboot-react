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

### RAG Chat with Memory — `RagMemoryChatController`
- `GET /rag/memory/ai/chat/string/client` — **active endpoint** used by the **RAG + Memory** tab; same RAG tuning params as above plus:
  - `conversationId` *(required)* — UUID string from the browser; scopes conversation history
- `DELETE /rag/memory/ai/chat/conversation/{conversationId}` — clears all stored history for a conversation (called when the user clicks "New Chat")

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
| 🧠 RAG + Memory | `RAGChatbotWithMemory.js` | `GET /rag/memory/ai/chat/string/client`, `DELETE /rag/memory/ai/chat/conversation/{id}` |
| 📄 Documents | `DocumentUpload.js` | `GET /documents`, `POST /documents/upload`, `DELETE /documents/{id}` |

## Key architecture notes

- **Two chat controllers**: `ChatController` calls the LLM directly with no document context. `RagChatController` calls `RagService.buildRagContext()` first to inject relevant document chunks as a system prompt before every LLM call.
- **Memory-augmented RAG**: `RagMemoryChatController` adds conversation memory on top of RAG. It uses a dedicated `memoryChatClient` bean wired with `MessageChatMemoryAdvisor`, which reads/writes history via `MessageWindowChatMemory` (last 20 messages). The conversation ID is passed per-request via the advisor param key `ChatMemory.CONVERSATION_ID` (`"chat_memory_conversation_id"`).
- `RagService.buildRagContext(message, topK, similarityThreshold, mode)` performs a PGVector similarity search and builds the system prompt. The no-arg overload delegates to this using values from `RagProperties`.
- `RagService.searchDocuments(query, topK, threshold)` is the raw search used by the Vector Search tab — returns matched chunks with similarity scores computed as `1 - distance`.
- `EmbeddingConfig` defines `TransformersEmbeddingModel` as `@Primary`, which prevents `OllamaEmbeddingModel` from being auto-configured. The ONNX model (`all-MiniLM-L6-v2`, 384 dims) is downloaded from HuggingFace on first use (~90 MB); subsequent starts use the cached copy.
- `IngestionService` uses `TikaDocumentReader` (Apache Tika — handles PDF, DOCX, TXT) → `TokenTextSplitter` → `VectorStore`. Document metadata is also persisted to the `document_metadata` table in PostgreSQL.
- Deletion removes rows from both `vector_store` (filtered by `metadata->>'filename'`) and `document_metadata`.
- `WebConfig` is the only CORS configuration; update `allowedOrigins` if the frontend URL changes (currently restricted to `http://localhost:3000`).
- The React app makes a **single non-streaming GET request** via axios. Switching to true SSE streaming would require `EventSource` or `fetch` with a `ReadableStream` in the chat components.
- All Java classes use Lombok `@Slf4j` for logging.
- There are **two `ChatClient` beans**: `chatClient` (plain, used by `RagChatController`) and `memoryChatClient` (wired with `MessageChatMemoryAdvisor`, used by `RagMemoryChatController`). Inject by name with `@Qualifier` to avoid ambiguity.

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
│   ├── RagMemoryChatController.java # /rag/memory/ai/chat/* (RAG + conversation memory)
│   └── DocumentController.java     # /documents/* including /verify and /verify/search
├── memory/
│   └── JdbcChatMemoryRepository.java # implements ChatMemoryRepository via JPA (PostgreSQL-backed)
├── model/
│   ├── DocumentInfo.java           # record returned by document list endpoint
│   ├── DocumentMetadata.java       # JPA entity for document_metadata table
│   └── ConversationMessage.java    # JPA entity for conversation_messages table
├── repository/
│   ├── DocumentMetadataRepository.java
│   └── ConversationMessageRepository.java
└── service/
    ├── RagService.java             # similarity search, prompt augmentation, vector store queries
    ├── RagMemoryService.java       # delegates to RagService; exposes clearConversation()
    └── IngestionService.java       # document parsing, chunking, vector storage
```

## Conversation memory

History is stored in the `conversation_messages` PostgreSQL table (added in Flyway migration V2). Each row holds one `USER` or `ASSISTANT` message with a `conversation_id` (UUID from the browser) and a `message_index` for ordering.

`JdbcChatMemoryRepository` implements Spring AI's `ChatMemoryRepository` interface:
- `saveAll(conversationId, messages)` — full replace: deletes existing rows then inserts the updated list (this matches Spring AI's contract — `MessageWindowChatMemory` passes the trimmed full list on every write)
- `findByConversationId(conversationId)` — returns all rows ordered by `message_index`
- `deleteByConversationId(conversationId)` — clears the conversation

`MessageWindowChatMemory` (window=20) wraps the JDBC repository. `MessageChatMemoryAdvisor` wraps the window memory and is registered as a default advisor on `memoryChatClient`. The prompt order the LLM sees per turn:

```
[SystemMessage: RAG doc chunks]
[UserMessage: turn N-K] / [AssistantMessage: turn N-K]
...
[UserMessage: current message]
```
