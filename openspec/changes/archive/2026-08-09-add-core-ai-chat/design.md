## Context

See `proposal.md` for motivation and `specs/core-ai-chat/spec.md` for the behavior contract. Pinny currently has a small FastAPI service, environment settings, structured redacted logging, direct PostgreSQL connectivity checks, and no application persistence layer, migrations, request identity, or external AI provider. The first chat capability crosses HTTP streaming, application orchestration, provider I/O, database transactions, and a temporary identity boundary.

## Goals / Non-Goals

**Goals:**
- Keep chat orchestration independent from FastAPI, SSE framing, OpenAI SDK types, and concrete database access.
- Make conversation ownership mandatory and enforce it in repository queries, not only in route code.
- Give successful, failed, and disconnected generations distinct durable states and client-visible terminal behavior.
- Establish migrations and persistence patterns that later Pinny capabilities can extend.
- Keep provider model selection, credentials, timeouts, and the basic system prompt configurable on the server.

**Non-Goals:**
- General authentication or authorization; the development identity adapter is an explicit temporary composition choice.
- Provider-managed conversation state. PostgreSQL remains the source of truth for conversation history.
- Multi-provider routing, automatic retries, background generation, replay/resume, usage billing, moderation pipelines, or guaranteed concurrent turns in one conversation.
- Any orchestration, retrieval, tool, file, memory, queue, or distributed-cache framework.

## Decisions

### Use application ports with thin infrastructure adapters

Define application-level interfaces for `CurrentUserProvider`, `ChatModel`, `ConversationRepository`, and `MessageRepository`. A chat service coordinates those ports and yields provider-neutral text deltas plus a terminal result. FastAPI dependencies compose development identity, PostgreSQL repositories, and the OpenAI adapter.

This keeps HTTP/SSE code responsible only for request/response translation and disconnect observation. It also prevents OpenAI SDK objects or persistence sessions from becoming application contracts. Direct SDK use in the route was rejected because it tightly couples validation, streaming, persistence, and provider behavior. LangChain was rejected because it adds no value for this single-provider boundary.

### Use the official async OpenAI SDK and Responses API behind `ChatModel`

The OpenAI adapter will use the async official SDK and a streaming Responses API request, normalize text delta and terminal/error events, and explicitly close or cancel the provider stream when the downstream client disconnects. The application supplies the full ordered input history and does not depend on OpenAI-hosted conversation state. This matches current official OpenAI guidance that the Responses API supports streaming event-based output while preserving provider replacement at the port boundary.

`PINNY_OPENAI_API_KEY`, `PINNY_OPENAI_MODEL`, and provider timeout settings remain server-only. The API key is represented as a secret configuration value and is never included in request schemas, SSE payloads, or log context. Model choice is configuration rather than a public chat parameter so clients cannot select an unexpectedly costly or unsupported model.

### Resolve identity before the application service

The HTTP dependency asks `CurrentUserProvider` for a non-empty opaque user ID and passes that value into the chat use case. The Phase 1 `DevelopmentCurrentUserProvider` reads `PINNY_DEV_USER_ID`; application and repository code cannot observe how it was resolved. Configuration validation refuses this provider when `PINNY_ENVIRONMENT` is production and clearly labels it development-only in documentation.

The request schema forbids unknown fields, which makes a supplied `user_id` a validation error rather than silently ignoring it. A later trusted Pinus authentication adapter can replace the provider without changing chat application APIs.

### Add SQLAlchemy async persistence and Alembic migrations

Use SQLAlchemy 2 async sessions over asyncpg and Alembic for explicit, reviewable schema evolution. Raw asyncpg queries were considered but rejected because the new relational model, transactions, constraints, and future migrations justify a small persistence layer.

Use PostgreSQL UUID primary keys and timezone-aware timestamps. `conversations` stores `id`, required `user_id`, `created_at`, and `updated_at`, with an index supporting owner-scoped lookup. `messages` stores `id`, `conversation_id`, `role`, `content`, `status`, and `created_at`, with foreign-key cascade behavior and a chronological `(conversation_id, created_at, id)` index. Database constraints restrict roles to `user`/`assistant` and statuses to the defined lifecycle values.

Repository lookup for a follow-up includes both conversation ID and resolved user ID. A missing or differently owned row maps to the same sanitized not-found response, preventing ownership enumeration.

### Model generation as an explicit message lifecycle

For an accepted request, one short database transaction creates or owner-loads the conversation, rejects an already active generation for that conversation, persists the completed user message, and creates an assistant placeholder with `in_progress` status. The transaction commits before contacting OpenAI so accepted user input is durable and no database transaction or row lock remains open during a network stream.

The service collects deltas in memory while yielding them. On a provider terminal-success event, a short transaction writes the full assistant content, changes its status to `completed`, and updates the conversation timestamp before the SSE completion event is emitted. If final persistence fails, the client receives an error event rather than a false completion.

On provider failure, timeout, or disconnect, cleanup changes the placeholder to `failed` or `interrupted` without marking it completed; partial text is not stored as completed history. Cleanup runs in a cancellation-protected short transaction and is idempotent. Follow-up history selects only completed messages, so failed output cannot contaminate context. The active `in_progress` marker also permits the application to reject overlapping generation for the same conversation with a conflict error; this is simpler and safer than allowing ambiguous concurrent history.

### Define a stable Pinny-owned SSE protocol

The endpoint returns `text/event-stream` and emits JSON payloads using these event names:
- `conversation`: emitted first with `conversation_id` and accepted user `message_id`.
- `delta`: ordered assistant text fragments.
- `completed`: emitted once after the completed assistant message commits, with conversation and assistant message identifiers.
- `error`: terminal sanitized code/message for a failure after streaming has begun.

Validation, identity, ownership, persistence, and concurrency failures discovered before the streaming response use structured JSON HTTP errors with suitable 4xx/5xx status codes. Once streaming begins, failures use a terminal SSE `error` because the HTTP status can no longer change. SSE formatting lives in the API adapter and escapes payloads through JSON serialization rather than interpolating provider text into protocol fields.

### Build context from durable completed messages

The application constructs model input from a basic version-controlled Pinny system prompt followed by completed conversation messages in stable chronological order. The current user message is already persisted and appears once at the end. Phase 1 sends the full completed history; configurable model/output limits and a clear context-limit error protect the provider call. Summarization, relevance selection, and long-term memory are deferred until there is evidence they are needed.

### Map failures at architectural boundaries

Application exceptions distinguish validation, conversation-not-found, generation-in-progress, persistence, provider configuration, provider timeout, provider failure, and downstream cancellation. The API owns stable public status/error codes; adapters retain diagnostic exception types for redacted structured logs. Provider response bodies, credentials, prompts, and message content are not logged by default.

## Risks / Trade-offs

- [Full history eventually exceeds model context] → Enforce configured limits and return a clear error now; add summarization or context selection in a later capability.
- [A process can die before marking an `in_progress` assistant message terminal] → Add a stale-generation recovery rule based on age and test it; never include `in_progress` rows in history.
- [Holding generated text in memory increases per-request memory] → Configure output limits; Phase 1 favors atomic completed-message persistence over partial-text durability.
- [Client disconnect detection and cancellation vary across ASGI servers] → Test cancellation at the service and transport boundaries and make terminal cleanup idempotent.
- [Development identity could be deployed accidentally] → Reject its composition in production and prominently document `PINNY_DEV_USER_ID` as non-production only.
- [No automatic retry reduces resilience to transient OpenAI failures] → Surface stable errors and metrics first; retries are deferred to avoid duplicate generations and complex streaming semantics.
- [Rejecting overlapping turns limits throughput per conversation] → Return a conflict response; reconsider only when product behavior for concurrent turns is defined.

## Migration Plan

1. Add dependencies and configuration with safe startup validation and documented development values.
2. Introduce Alembic and apply the conversation/message migration before enabling the route.
3. Deploy the ports, adapters, application service, and API route with mocked-provider tests and real PostgreSQL integration coverage.
4. Verify successful streaming, ownership denial, provider failure, disconnect cleanup, and stale `in_progress` recovery in a non-production environment using a development identity.
5. Roll back by disabling/removing the chat route and application code first; retain the additive tables during rollback to avoid conversation loss. Drop them only through a later explicit data-retention decision.
