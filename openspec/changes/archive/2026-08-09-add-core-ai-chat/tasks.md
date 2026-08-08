## 1. Dependencies and Configuration

- [x] 1.1 Add the OpenAI SDK, SQLAlchemy async, Alembic, and SSE-related project dependencies
- [x] 1.2 Add typed server-only settings for the OpenAI API key, model, timeouts, output/context limits, and `PINNY_DEV_USER_ID`
- [x] 1.3 Add configuration validation that requires a non-empty development identity and rejects the development identity provider in production
- [x] 1.4 Update environment and Compose templates without exposing OpenAI credentials to images, logs, or clients

## 2. Database Persistence

- [x] 2.1 Configure SQLAlchemy async sessions over the existing PostgreSQL settings and integrate Alembic migrations
- [x] 2.2 Define conversation and message persistence models with UUIDs, required ownership, role/status constraints, timestamps, foreign keys, and lookup indexes
- [x] 2.3 Create and validate the initial Alembic migration for conversation and message tables, including downgrade behavior
- [x] 2.4 Implement owner-scoped conversation and chronological completed-message repositories with transactional create/follow-up operations
- [x] 2.5 Implement idempotent assistant lifecycle transitions for `in_progress`, `completed`, `failed`, and `interrupted`, plus stale-generation recovery

## 3. Identity and Application Boundaries

- [x] 3.1 Define provider-neutral current-user, chat-model, repository, message/event, and application-error interfaces
- [x] 3.2 Implement the configuration-backed development current-user provider and FastAPI dependency composition
- [x] 3.3 Implement the basic version-controlled Pinny system prompt and deterministic chronological history construction using completed messages only
- [x] 3.4 Implement chat preparation that creates or owner-loads a conversation, rejects unauthorized/unknown/active conversations, and persists the user and assistant placeholder before generation
- [x] 3.5 Implement streaming orchestration that yields normalized deltas, commits the completed assistant response before completion, and finalizes failures or interruptions safely

## 4. OpenAI Provider

- [x] 4.1 Implement the async OpenAI Responses API adapter behind the chat-model interface with configured model, limits, and timeouts
- [x] 4.2 Normalize OpenAI streaming events and ensure provider streams close on success, failure, timeout, and cancellation
- [x] 4.3 Add redacted provider diagnostics and sanitized mappings for missing configuration, authentication, rate-limit, timeout, and upstream failures

## 5. HTTP and SSE API

- [x] 5.1 Add the strict `POST /api/v1/chat` request schema with optional conversation ID, non-empty message, and forbidden unknown fields such as `user_id`
- [x] 5.2 Implement the versioned chat route with pre-stream identity, ownership, persistence, and concurrency error handling
- [x] 5.3 Implement JSON-encoded SSE framing for `conversation`, `delta`, `completed`, and terminal `error` events
- [x] 5.4 Detect client disconnects, cancel provider work, run cancellation-protected interruption cleanup, and suppress completion events
- [x] 5.5 Register stable structured JSON and SSE error codes without leaking credentials, provider bodies, prompts, or message content

## 6. Tests and Validation

- [x] 6.1 Add unit tests for settings safety, development identity behavior, request validation, and system-prompt/history ordering
- [x] 6.2 Add application tests for new and follow-up conversations, owner isolation, missing conversations, concurrent-turn rejection, and pre-generation persistence failure
- [x] 6.3 Add provider-adapter tests for ordered deltas, completion, timeout, upstream errors, and stream cancellation using mocked OpenAI responses
- [x] 6.4 Add API/SSE tests for event ordering and framing, successful completion, pre-stream HTTP errors, mid-stream errors, and client disconnects
- [x] 6.5 Add PostgreSQL integration tests for migrations, constraints, persistence, completed-history filtering, lifecycle cleanup, and stale-generation recovery
- [x] 6.6 Run Ruff formatting/linting, the full pytest suite, migration upgrade/downgrade validation, and a containerized streaming smoke test

## 7. Documentation

- [x] 7.1 Document the chat request schema, SSE event contract, stable error behavior, and conversation ownership rules
- [x] 7.2 Document OpenAI and chat configuration with secret-handling guidance and clearly label `PINNY_DEV_USER_ID` as non-production only
- [x] 7.3 Document migration, local startup, streaming test, failure simulation, and quality-validation workflows
- [x] 7.4 Update architecture documentation with HTTP, application, identity, persistence, and replaceable LLM-provider boundaries and the Phase 1 exclusions
