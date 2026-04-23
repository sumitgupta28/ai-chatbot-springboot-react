# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository layout

Two independently deployable services:

```
spring-boot-ai-chatbot/   # Spring Boot 3.5 + Spring AI 1.1.4 backend
chatbot-ui/               # React 18 frontend (Create React App)
docker-compose.yaml       # Orchestrates both services
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

Listens on **port 8080**.

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
```

Copy `.env.example` → `.env` for environment variables.

## AI model profiles

The backend uses **Spring AI's `ChatModel` interface** — the active provider is selected via `spring.ai.model.chat` in config.

| Profile | Provider | Config file | Required env var |
|---|---|---|---|
| *(default)* | Ollama (local) | `application.yaml` | none — Ollama at `http://localhost:11434` |
| `anthropic` | Anthropic Claude | `application-anthropic.yaml` | `ANTHROPIC_API_KEY` |

`ChatController` is provider-agnostic; it injects `ChatModel` (the Spring AI interface), so it works with either profile unchanged.

When adding a new provider, add its `spring-ai-starter-model-*` dependency to `build.gradle`, create an `application-<profile>.yaml` with `spring.ai.model.chat: <provider>`, and activate it via `--spring.profiles.active=<profile>`.

## API endpoints

Both endpoints accept `?message=<text>` and return a reactive stream (`Flux`).

- `GET /ai/chat` — streams full `ChatResponse` objects (JSON)
- `GET /ai/chat/string` — streams plain text tokens

The React frontend (`Chatbot.js`) calls `/ai/chat/string` via axios and renders the full response once resolved. CORS is restricted to `http://localhost:3000`.

## Key architecture notes

- `ChatController` calls `chatModel.stream(prompt)` — always streaming, never blocking.
- `WebConfig` is the only CORS configuration; update `allowedOrigins` if the frontend URL changes.
- The React app makes a **single non-streaming GET request** via axios (it waits for the full response). Switching to true SSE streaming would require changing `Chatbot.js` to use `EventSource` or `fetch` with a `ReadableStream`.
- Docker Compose passes `SPRING_AI_OLLAMA_BASE_URL` to override the Ollama URL inside containers (`host.docker.internal:11434` by default, since Ollama runs on the host).
