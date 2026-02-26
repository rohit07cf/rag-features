# Engineering Notes — Production Hardening Refactor

This document captures the design decisions, architectural patterns, and tradeoffs
made during the production-hardening refactor of the RAG Assistant Studio.

---

## Layered Architecture

The codebase follows a **three-layer architecture** with strict dependency direction:

```
API Layer  →  Domain Layer  →  Infrastructure Layer
(routes)      (services,        (repos, adapters,
               pipelines,        external clients)
               protocols)
```

- **API Layer** (`src/app/api/`): Thin FastAPI routes that parse requests, call
  domain services, and format responses. No business logic lives here.
- **Domain Layer** (`src/domain/`): Services, pipelines, models, protocols, and
  error types. This layer owns the business rules and is framework-agnostic.
- **Infrastructure Layer** (`src/app/storage/`, `src/rag/`): Concrete implementations
  of vector stores, embedders, LLM clients, and database repositories.

### Why This Separation?

Routes that contain business logic become untestable monoliths. By pushing logic
into services, we can unit-test domain behavior with fakes/mocks, independent of
HTTP or database concerns.

---

## Design Patterns

| Pattern | Where | Purpose |
|---------|-------|---------|
| **Strategy** | `ChunkingStrategy` + `get_chunker()` registry | Swap chunking algorithms without touching callers |
| **Strategy** | `Reranker` protocol + `LocalReranker` / `ExternalReranker` | Pluggable reranking backends |
| **Factory** | `create_llm()` in `factory.py`, `get_chunker()` in `base.py` | Centralize object creation, isolate constructor details |
| **Adapter** | `OpenAILLM`, `AnthropicLLM`, `PineconeStore`, `OpenAIEmbedder` | Wrap external SDKs behind domain protocols |
| **Repository** | `assistants_repo.py` | Single point of database access with query encapsulation |
| **Facade** | `ChatService` | Hides memory, retrieval, prompt building, and LLM call behind `chat_model_only()` / `chat_rag()` |
| **Template Method** | `RetrievalPipeline.run()` | Fixed 4-stage pipeline (embed → search → rerank → budget) with pluggable components |
| **Command** | `AssistantCreateCommand`, `IngestionCommand`, `ChatCommand` | Typed request objects that travel between layers |
| **Composition Root** | `src/app/container.py` | Single place that wires all dependencies; no other module instantiates external clients |

---

## Domain Models

### Pydantic Everywhere

All domain models are Pydantic `BaseModel` subclasses:

- **`Chunk`** — Replaced the original dataclass. Preserves `to_dict()` for
  backward compatibility with workflow activities.
- **`AssistantCreateCommand`**, **`ChatCommand`**, **`IngestionCommand`** — Typed
  command objects that travel between layers.
- **`Settings`** — Pydantic `BaseSettings` with validators (log_level pattern,
  upload size bounds, property helpers for config checks).

### Typed Enums

Stringly-typed fields were replaced with `str, Enum` subclasses:

- `AssistantType` — `model_only | rag`
- `LLMProvider` — `openai | anthropic`
- `ChunkStrategy` — `recursive | token | heading_aware | adaptive | contextual_docintel`
- `IngestionState` — `pending | running | succeeded | failed`
- `IngestionStep` — `pending | extracting | cleaning | chunking | embedding | upserting | succeeded | failed`

Enums in Pydantic schemas (`AssistantCreate`) give us free validation — FastAPI
returns 422 with a clear error message when an invalid value is submitted.

---

## Error Taxonomy

```
AppError (base)
├── NotFoundError    → HTTP 404
├── ValidationError  → HTTP 400
├── ExternalServiceError → HTTP 502
└── ConfigError      → HTTP 500
```

Domain services raise typed `AppError` subclasses. FastAPI exception handlers in
`main.py` map them to structured JSON responses with `error_code`, `message`, and
`details` fields.

**Tradeoff:** Routes can still raise `HTTPException` for route-level concerns
(e.g., 422 from Pydantic). Domain errors handle domain-level concerns. This avoids
coupling domain services to FastAPI.

---

## Protocol-Based Dependency Inversion

Domain services depend on `typing.Protocol` interfaces, not concrete classes:

- `LLMClient` — `agenerate()`, `provider_name`, `model_name`
- `VectorStore` — `upsert_vectors()`, `query()`
- `Embedder` — `embed_texts()`, `embed_query()`, `dimension`
- `Reranker` — `rerank()`
- `ConversationMemory` — `add_message()`, `get_history()`, `clear()`

Concrete implementations (`OpenAILLM`, `PineconeStore`, etc.) structurally satisfy
these protocols without inheriting from them. This means:

1. **Testability** — Tests inject fakes that implement the protocol.
2. **Swappability** — Replace Pinecone with Qdrant by implementing `VectorStore`.
3. **No import cycles** — Domain layer never imports infrastructure.

---

## Composition Root

`src/app/container.py` is the **single place** that wires infrastructure to domain:

```python
def get_chat_service():
    return ChatService(
        memory=get_memory(),
        retrieval_pipeline=get_retrieval_pipeline(),
    )
```

Routes call container functions to get fully assembled services. This keeps
route files thin and makes it trivial to swap implementations for testing or
different environments.

---

## Service Layer

### ChatService (Facade)

`ChatService` hides the complexity of two chat paths:

- `chat_model_only()` — system prompt → history → LLM call → memory store
- `chat_rag()` — retrieval pipeline → prompt building → LLM call → memory → source formatting

Before the refactor, all this logic lived in `routes_chat.py` (120+ lines).
Now the route is ~20 lines of delegation.

### IngestionService

Handles upload validation, file persistence, and Temporal workflow dispatch.
Extracted from `routes_documents.py` and `routes_ingestions.py`.

### AssistantsService

Thin wrapper around the repository with domain-level `NotFoundError` raising.
Keeps the repository layer unaware of error semantics.

---

## Chunker Registry (Strategy + Factory)

The centralized `get_chunker()` function in `src/rag/chunking/base.py` replaces
the duplicated `_get_chunker()` that lived in `chunk_text.py` (Temporal activity).

```python
def get_chunker(strategy: str) -> ChunkingStrategy:
    registry = {
        "recursive": RecursiveChunker,
        "token": TokenChunker,
        ...
    }
    cls = registry.get(strategy, RecursiveChunker)
    return cls()
```

**Benefits:**
- Single source of truth for strategy → class mapping
- Adding a new chunker means one registry entry + one class
- Activity code is now two lines instead of a 20-line if/elif chain

---

## Tradeoffs and Known Issues

1. **`InMemoryStore` is not production-ready.** It's a `defaultdict(list)` with
   class-level state. Replace with Redis or database-backed store for production.

2. **Temporal workflow_id in ingestion records.** The `update_ingestion_state()`
   function doesn't accept `workflow_id` as a parameter. The service code wraps
   the call in a try/except so this is handled gracefully, but a migration to
   add workflow_id tracking would be a good follow-up.

3. **Enum values in SQLModel.** The SQLite `Assistant` model stores type/provider
   as plain strings. The enum validation happens at the API schema layer. A future
   improvement could use SQLAlchemy `Enum` columns for database-level enforcement.

4. **Cross-encoder model download.** `LocalReranker` attempts to load
   `ms-marco-MiniLM-L-6-v2` at instantiation. In CI/offline environments, it
   falls back to score-based sorting. This is intentional.

---

## Test Coverage

| Test File | Scope | Count |
|-----------|-------|-------|
| `test_services.py` | ChatService, IngestionService, AssistantsService | 16 |
| `test_retrieval_pipeline.py` | RetrievalPipeline with fakes | 3 |
| `test_error_handlers.py` | Exception handler HTTP mapping | 4 |
| `test_api_smoke.py` | End-to-end API routes | 6 |
| `test_assistants_api.py` | Repository CRUD + rag_status | 7 |
| `test_chunkers.py` | All 4 chunking strategies | 11 |
| `test_metadata.py` | Chunk model + contextual chunker | 6 |
| `test_reranker.py` | Local + external rerankers | 4 |
| `test_llm_factory.py` | LLM factory + model resolution | 8 |
| `test_workflow_unit.py` | Activity logic + chunker registry | 9 |
| **Total** | | **74** |

All tests run without external services (no API keys, no Temporal server, no Pinecone).
