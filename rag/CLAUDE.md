# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RAG-Restaurante is a Retrieval-Augmented Generation system for restaurant menu queries with emphasis on allergen safety. Uses local LLM inference via Ollama and vector search via PostgreSQL/pgvector.

## Commands

```bash
# Setup
docker compose up -d                    # Start PostgreSQL (port 5434)
pip install -r requirements.txt         # Install dependencies
ollama pull nomic-embed-text            # Required embedding model
ollama pull llama3.2:1b                 # Default chat model
# Note: Database tables are created automatically on first app startup

# Development
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Testing
pytest                                  # All tests
pytest tests/unit/                      # Unit tests only
pytest tests/unit/test_text_service.py  # Single test file
pytest -k "test_normalize"              # Tests matching pattern
pytest --cov=src                        # With coverage

# Linting (configured in pyproject.toml)
ruff check src/                         # Lint check
ruff check src/ --fix                   # Auto-fix issues
mypy src/                               # Type checking
```

## Architecture

**Layered architecture** with dependency injection via FastAPI `Depends()`:

```
API Layer (src/api/)           → Thin routers, request validation
    ↓
Service Layer (src/services/)  → Business logic orchestration
    ↓
Repository Layer (src/repositories/) → Data access abstraction
    ↓
Models Layer (src/models/)     → SQLAlchemy entities
```

### RAG Data Flow

1. **Indexing**: Dishes → `TextService.chunk()` → `OllamaService.generate_embedding()` → pgvector
2. **Query**: Question → Embed → `EmbeddingRepository.search_similar()` → `RetrievalService` (confidence scoring) → `PromptService` → LLM → Response

### Key Services

- **ChatService** (`src/services/chat_service.py`): Orchestrates RAG flow
- **RetrievalService**: Semantic search + confidence-based decision routing (thresholds: 0.78 answer, 0.60 soft_disclaimer)
- **OllamaService**: HTTP client for Ollama API with timeout handling
- **TextService**: Text normalization, chunking (1200 chars, 200 overlap), allergy keyword detection
- **PromptService**: Spanish-language prompt construction with allergen safety emphasis

### Decision Logic

Located in `src/services/retrieval_service.py`:
- `confidence >= 0.78` → `DecisionType.ANSWER`
- `confidence >= 0.60` → `DecisionType.SOFT_DISCLAIMER`
- Otherwise → `DecisionType.DISCLAIMER`

## Configuration

All settings in `src/config/settings.py` (Pydantic Settings, loads from `.env`):

| Setting | Default | Purpose |
|---------|---------|---------|
| `DATABASE_URL` | `postgresql+psycopg://...@127.0.0.1:5434/menu_rag` | DB connection |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama endpoint |
| `EMBED_MODEL` | `nomic-embed-text` | Embedding model (768-dim) |
| `CHAT_MODEL` | `llama3.2:1b` | LLM for responses |
| `confidence_answer_threshold` | `0.78` | High confidence cutoff |
| `confidence_soft_threshold` | `0.60` | Medium confidence cutoff |

## Database Schema

5 tables in `src/models/entities.py`:
- **dish**: Menu items (name, category, price_cents, tags)
- **kb_chunk**: Text chunks from dish descriptions (content, chunk_index)
- **kb_embedding**: 768-dim vectors (pgvector)
- **chat_turn**: Conversation history
- **rag_trace**: Audit trail (used_chunk_ids, scores, decision)

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | System status (DB counts, Ollama reachability) |
| GET | `/dishes` | List all active dishes |
| POST | `/chat` | RAG query endpoint (question, optional dish_id, top_k) |
| POST | `/seed` | Load sample dishes (idempotent) |
| POST | `/index` | Generate embeddings for unindexed chunks |

## Development Notes

- Port 5434 avoids conflicts with local Windows PostgreSQL
- Chat endpoint has 300s timeout for large model inference
- Allergy queries trigger conservative mode (see `ALLERGY_TRIGGERS` in `src/core/constants.py`)
- Add new dishes via `data/seed_dishes.py` using `_dish_template()` function
- All prompts and responses are in Spanish

## V2 Roadmap

See `optimizacion.md` for the detailed production evolution plan, including:
- Multi-tenant/multi-branch architecture
- Semantic chunking by sections (INGREDIENTS, ALLERGENS, TRACES, etc.)
- Risk-based policies per intent type (0.85 threshold for allergens)
- Structured JSON responses (AnswerEnvelope)
- Document lifecycle management (DRAFT → PUBLISHED → ARCHIVED)
