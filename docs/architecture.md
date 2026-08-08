# Pinny Architecture

## System context

```text
Pinus Flutter → Pinus NestJS → Pinny FastAPI → OpenAI or Gemini
                                  ↓
                              PostgreSQL
```

Pinny is independently deployable and does not own Pinus business data. Future Pinus data
access must use trusted, defined interfaces.

## Core AI chat boundaries

- **HTTP adapter (`api`)** validates public input, resolves current identity, maps errors, and
  frames Pinny-owned SSE events. It does not orchestrate OpenAI or database transactions.
- **Application chat (`chat`)** owns conversation orchestration, system prompt/history ordering,
  assistant lifecycle rules, and provider-neutral ports.
- **Identity adapter** currently resolves `PINNY_DEV_USER_ID`. It is development-only and can be
  replaced by trusted Pinus authentication without changing the chat use case.
- **LLM provider factory** selects OpenAI or Gemini once from validated startup configuration.
  `ChatService` receives only the provider-neutral model port and contains no vendor branching.
- **LLM adapters** map vendor streams and terminal states to ordered text deltas and sanitized
  application errors. SDK types, credentials, and response bodies do not escape this boundary.
- **Persistence adapter (`db`)** uses SQLAlchemy async sessions and PostgreSQL. Alembic owns
  schema evolution; repositories enforce conversation ownership in their queries.

## Data ownership and lifecycle

Every conversation has a required current-user owner. User messages are committed before model
generation. An assistant placeholder moves from `in_progress` to `completed`, `failed`, or
`interrupted`; only completed messages form later model context. Completion is sent only after
the assistant content commits.

Unknown and differently owned conversation IDs share the same not-found response. Concurrent
turns in one conversation are rejected while an assistant message is active. Stale active rows
are recovered as interrupted.

## Security boundary

Provider credentials are server-only secret settings. Public requests cannot supply identity,
provider, or model choice. Logs omit prompts/message content and redact secrets/provider details. The
development identity provider is rejected in production configuration.

## Phase 1 exclusions

No provider fallback, automatic routing, load balancing, LangChain, LangGraph, RAG, embeddings,
pgvector retrieval, Pinus tool calling, file handling, personal memory, recommendation pipelines,
Redis, or Celery are introduced.
