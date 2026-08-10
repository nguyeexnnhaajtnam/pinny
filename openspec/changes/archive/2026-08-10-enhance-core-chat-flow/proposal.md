## Why

Pinny's standalone chat works end-to-end, but it currently sends unbounded completed history, has a minimal prompt path, and exposes only coarse provider failure and generation metadata. Hardening these boundaries now keeps the public chat API stable while making later Pinus context, RAG, and memory additions possible without rewriting `ChatService`.

## What Changes

- Add provider-neutral runtime context for current date, datetime, timezone, and locale using standalone configuration defaults; runtime context is deterministic and is never persisted as a chat message.
- Add explicit prompt and conversation-context builders that separate system instructions, runtime context, bounded chronological history, and the current user turn.
- Apply a configurable recent-message history policy without summarization or semantic memory.
- Make assistant generation states and transitions explicit across pending, streaming, completed, failed, and cancelled outcomes, including client disconnect behavior and migration from existing statuses.
- Formalize the existing `conversation`, `delta`, `completed`, and `error` SSE events with consistent conversation/message identifiers and provider-neutral safe errors.
- Normalize OpenAI and Gemini failures into application-level LLM errors and add bounded, configurable retries only for safe transient failures.
- Persist basic provider-neutral generation metadata: provider, model, latency, status, and token usage when supplied by the provider.
- Expand automated contract, lifecycle, context, error, retry, persistence, ownership, and provider-adapter coverage while keeping real-provider verification manual.
- Preserve `POST /api/v1/chat`, the development current-user mechanism, conversation ownership, PostgreSQL, and configurable OpenAI/Gemini providers.
- Explicitly exclude Pinus integration, tools, RAG, embeddings, files, memory, routing/fallback, LangChain, LangGraph, Redis, and Celery.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `core-ai-chat`: Adds deterministic runtime context, bounded prompt/context assembly, explicit generation lifecycle and metadata, and a fully specified provider-neutral SSE contract while preserving ownership and the public request API.
- `llm-provider-configuration`: Adds normalized provider errors, explicit timeout behavior, bounded safe-retry policy, and equivalent provider metadata reporting to the shared LLM contract.

## Impact

- Affects chat orchestration ports/types, prompt construction, repository queries and lifecycle transitions, OpenAI/Gemini adapters, configuration, SSE encoding, database models/migrations, tests, and developer documentation.
- Requires an additive/migrating PostgreSQL schema change for explicit lifecycle states and generation metadata; existing conversations and completed messages remain valid.
- Does not change the public chat request shape or introduce a new external service or orchestration framework.
