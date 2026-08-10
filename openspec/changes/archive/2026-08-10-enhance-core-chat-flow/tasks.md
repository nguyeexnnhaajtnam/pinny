## 1. Configuration and runtime context

- [x] 1.1 Extend application settings with validated standalone timezone, locale, bounded `CHAT_HISTORY_MAX_MESSAGES`, generation timeout, and finite retry configuration, including safe defaults and startup failures for invalid values.
- [x] 1.2 Add immutable runtime-context types and a `RuntimeContextProvider` port that exposes the current aware datetime, date, IANA timezone, and locale without depending on HTTP or LLM provider code.
- [x] 1.3 Implement the standalone configuration-backed runtime-context provider with an injectable clock, and wire it into application startup and chat-service construction.
- [x] 1.4 Add unit tests for deterministic runtime context, timezone conversion, locale defaults, and invalid timezone/locale configuration.

## 2. Conversation context and prompt construction

- [x] 2.1 Add a `ConversationContextBuilder` that selects only completed messages, enforces the configured recent-message limit, restores chronological order, and appends the current user message exactly once.
- [x] 2.2 Update repository queries and service inputs so persisted history is fetched separately from the newly accepted user message and bounded efficiently at the database layer.
- [x] 2.3 Add a provider-neutral `PromptBuilder` that constructs distinct system, runtime-context, conversation-history, and current-user sections without provider-specific formatting in `ChatService`.
- [x] 2.4 Keep optional future context sources absent by default while defining extension points for later Pinus, RAG, and memory context.
- [x] 2.5 Add unit tests covering first-turn prompts, follow-up prompts, history truncation, chronological ordering, exclusion of failed/incomplete messages, and non-persistence of runtime context.

## 3. Provider-neutral streaming, errors, and retry policy

- [x] 3.1 Extend the LLM provider abstraction to emit typed text deltas and one terminal generation result containing provider, model, and optional token usage.
- [x] 3.2 Introduce normalized application-level LLM errors for rate limits, timeouts, unavailability, invalid requests, configuration/authentication failures, and unexpected provider failures.
- [x] 3.3 Map OpenAI streaming responses, terminal metadata, and SDK errors into the provider-neutral contract without leaking raw provider payloads.
- [x] 3.4 Map Gemini streaming responses, terminal metadata, and SDK errors into the same provider-neutral contract without leaking raw provider payloads.
- [x] 3.5 Implement configurable generation timeout and bounded retry behavior that retries only eligible failures before the first emitted delta and never retries cancellation, invalid request, authentication, or configuration errors.
- [x] 3.6 Ensure provider streams and clients are closed or cancelled on timeout, failure, retry, and caller cancellation.
- [x] 3.7 Add provider contract tests for OpenAI and Gemini covering equivalent deltas, terminal metadata, normalized failures, timeout, retry success, retry exhaustion, and non-retryable failures.

## 4. Message lifecycle and generation metadata persistence

- [x] 4.1 Update the message domain/database model to use `pending`, `streaming`, `completed`, `failed`, and `cancelled` lifecycle states and add nullable provider, model, latency, input-token, and output-token metadata fields for assistant generations.
- [x] 4.2 Add an Alembic migration that maps existing `in_progress` rows to `streaming`, maps `interrupted` rows to `cancelled`, adds generation metadata columns, and provides a tested downgrade path.
- [x] 4.3 Add repository operations for atomic user-message plus pending-assistant creation and guarded lifecycle transitions from pending to streaming and from active states to exactly one terminal state.
- [x] 4.4 Persist completed assistant content and available generation metadata atomically only after provider generation completes successfully.
- [x] 4.5 Persist normalized failure state for generation errors, mark client-disconnected generations as cancelled, retain partial content only as non-completed data, and prevent terminal-state races from overwriting one another.
- [x] 4.6 Define and implement startup or maintenance handling for stale active-generation rows so they cannot be mistaken for completed responses.
- [x] 4.7 Add repository and migration tests for every lifecycle transition, invalid transition, legacy-state mapping, metadata with and without token usage, partial failure, cancellation, and concurrent terminal updates.

## 5. Chat orchestration and SSE contract

- [x] 5.1 Refactor `ChatService` to orchestrate identity ownership checks, runtime context, bounded history, prompt construction, provider generation, retry policy, latency measurement, and lifecycle persistence through application-level abstractions.
- [x] 5.2 Preserve the public `POST /api/v1/chat` request schema and development `CurrentUserProvider`, ensuring `user_id` remains absent from request payloads and conversation ownership is enforced.
- [x] 5.3 Formalize SSE serialization for only `conversation`, `delta`, `completed`, and `error` events with stable conversation/message identifiers and provider-neutral payloads.
- [x] 5.4 Emit `completed` only after the completed assistant message and metadata have been committed; emit normalized safe error codes/messages for failures without exposing credentials, SDK exceptions, or provider response bodies.
- [x] 5.5 Handle client disconnects and iterator cancellation explicitly so provider work stops, the assistant message becomes cancelled, no completed event is emitted, and cleanup remains idempotent.
- [x] 5.6 Add service and API tests for successful first/follow-up turns, event ordering and identifiers, persistence-before-completion, partial-stream failure, pre-stream retry, timeout, disconnect cancellation, ownership rejection, and request validation.

## 6. Integration verification and documentation

- [x] 6.1 Add PostgreSQL-backed integration tests for bounded history selection, lifecycle persistence, generation metadata, and completed-message context filtering.
- [x] 6.2 Update `.env.example` and developer configuration documentation for runtime context, history limits, timeout, retry controls, and their standalone/non-production identity behavior.
- [x] 6.3 Update API documentation with the unchanged request schema, formal SSE event examples, normalized error codes, message lifecycle semantics, and client-disconnect behavior.
- [x] 6.4 Document manual OpenAI and Gemini live SSE plus PostgreSQL smoke-test steps, including how to verify persisted lifecycle state and metadata without recording secrets.
- [x] 6.5 Run the complete unit and integration test suites, static checks, migration upgrade/downgrade verification, and container startup validation for both supported provider configurations.
