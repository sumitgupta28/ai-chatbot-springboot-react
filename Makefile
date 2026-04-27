.PHONY: help up down build rebuild logs ps \
        up-ollama up-anthropic \
        db migrate \
        backend-dev frontend-dev \
        clean clean-volumes clean-all

# ── Default LLM provider ────────────────────────────────────────────────────
LLM_PROVIDER     ?= ollama
OLLAMA_CHAT_MODEL ?= llama3.2
ANTHROPIC_CHAT_MODEL ?= claude-sonnet-4-6

# Export so docker compose picks them up
export LLM_PROVIDER
export OLLAMA_CHAT_MODEL
export ANTHROPIC_CHAT_MODEL
export ANTHROPIC_API_KEY

# ── Help ────────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  AI Chatbot — Docker targets"
	@echo ""
	@echo "  Full stack"
	@echo "    make up              Start all services (Ollama LLM, default)"
	@echo "    make up-anthropic    Start all services with Anthropic Claude"
	@echo "    make down            Stop all services"
	@echo "    make build           Build all Docker images (no cache)"
	@echo "    make rebuild         Build + start (no cache)"
	@echo "    make logs            Tail logs for all services"
	@echo "    make ps              Show running containers"
	@echo ""
	@echo "  Database"
	@echo "    make db              Start only PGVector (for local dev)"
	@echo "    make migrate         Run Alembic migrations against localhost DB"
	@echo ""
	@echo "  Local dev (no Docker)"
	@echo "    make backend-dev     Start FastAPI backend with hot-reload"
	@echo "    make frontend-dev    Start React dev server"
	@echo ""
	@echo "  Cleanup"
	@echo "    make clean           Remove stopped containers and dangling images"
	@echo "    make clean-volumes   Also delete the pgvector_data volume (⚠ data loss)"
	@echo "    make clean-all       Full reset: images + volumes + build cache"
	@echo ""
	@echo "  Variables (override on the command line)"
	@echo "    LLM_PROVIDER         ollama | anthropic  (default: ollama)"
	@echo "    ANTHROPIC_API_KEY    Required when LLM_PROVIDER=anthropic"
	@echo "    OLLAMA_CHAT_MODEL    Ollama model name  (default: llama3.2)"
	@echo "    ANTHROPIC_CHAT_MODEL Anthropic model    (default: claude-sonnet-4-6)"
	@echo ""

# ── Full-stack Docker Compose ────────────────────────────────────────────────

## Start all services with Ollama (default)
up:
	docker compose up -d
	@echo ""
	@echo "  Services started:"
	@echo "    Frontend  → http://localhost:3000"
	@echo "    Backend   → http://localhost:8080"
	@echo "    PGVector  → localhost:5432"
	@echo ""
	@echo "  Run 'make logs' to follow logs."

## Start all services with Anthropic Claude
up-anthropic:
	@if [ -z "$(ANTHROPIC_API_KEY)" ]; then \
		echo "ERROR: ANTHROPIC_API_KEY is not set."; \
		echo "  Run: ANTHROPIC_API_KEY=sk-ant-... make up-anthropic"; \
		exit 1; \
	fi
	LLM_PROVIDER=anthropic docker compose up -d
	@echo ""
	@echo "  Services started with Anthropic Claude ($(ANTHROPIC_CHAT_MODEL))."

## Stop all services
down:
	docker compose down

## Build all images (no cache)
build:
	docker compose build --no-cache

## Build + start (no cache)
rebuild:
	docker compose down
	docker compose build --no-cache
	docker compose up -d

## Tail logs for all services
logs:
	docker compose logs -f

## Show running containers
ps:
	docker compose ps

# ── Database ─────────────────────────────────────────────────────────────────

## Start only PGVector (for running backend locally outside Docker)
db:
	docker compose up pgvector -d
	@echo "PGVector ready on localhost:5432  (db=ragdb, user=postgres, pass=postgres)"

## Run Alembic migrations against localhost DB
migrate:
	cd chatbot-backend && alembic upgrade head

# ── Local dev (without Docker) ───────────────────────────────────────────────

## Start FastAPI backend with hot-reload (requires PGVector running)
backend-dev:
	cd chatbot-backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

## Start React dev server
frontend-dev:
	cd chatbot-ui && npm start

# ── Cleanup ──────────────────────────────────────────────────────────────────

## Remove stopped containers and dangling images
clean:
	docker compose down --remove-orphans
	docker image prune -f

## Remove stopped containers, images, and the pgvector data volume (DATA LOSS)
clean-volumes:
	docker compose down --volumes --remove-orphans
	docker image prune -f

## Full reset: remove containers, volumes, images, and Docker build cache
clean-all:
	docker compose down --volumes --remove-orphans
	docker system prune -af
