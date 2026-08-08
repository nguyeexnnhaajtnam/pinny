## Why

Pinny needs its first user-facing AI capability so Pinus can support basic contextual conversations. Building the chat contract now establishes secure identity, persistence, streaming, and provider boundaries before more advanced intelligence features are introduced.

## What Changes

- Integrate OpenAI behind an application-level LLM provider abstraction with server-only credential configuration.
- Add `POST /api/v1/chat` with validated input and Server-Sent Events streaming.
- Create and persist user-owned conversations and their user/assistant messages in PostgreSQL.
- Supply persisted conversation history and a basic Pinny system prompt to follow-up generations.
- Introduce a request identity abstraction; Phase 1 uses a clearly non-production configuration-backed development user and never accepts `user_id` in the public chat payload.
- Enforce conversation ownership for follow-up messages.
- Define explicit persistence and client behavior for provider failures and interrupted streams so incomplete generations are not recorded as completed assistant messages.
- Add chat, persistence, streaming, ownership, and failure-path tests and update API/developer documentation.
- Keep LangChain, LangGraph, RAG, embeddings, pgvector retrieval, Pinus tool calling, files, personal memory, recommendation pipelines, Redis, and Celery out of scope.

## Capabilities

### New Capabilities
- `core-ai-chat`: provide identity-scoped, persistent, contextual AI conversations through a validated SSE streaming API.

### Modified Capabilities
- None.

## Impact

This change adds a versioned chat API, OpenAI SDK dependency and configuration, PostgreSQL schema and migrations for conversations/messages, identity and LLM provider ports, chat orchestration, SSE transport behavior, and corresponding tests and documentation. OpenAI credentials remain server-side, Pinus authentication integration remains replaceable, and the existing service-foundation behavior is preserved.
