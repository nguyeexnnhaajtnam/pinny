## Context

The current flow already separates HTTP/SSE, `ChatService`, persistence, and OpenAI/Gemini adapters. However, repositories currently return all completed history, system prompting is a single helper, provider streams yield only strings, assistant lifecycle uses `in_progress/completed/failed/interrupted`, and provider metadata/error categories are too coarse for the requested behavior. This is a cross-cutting hardening change with a database migration; see `proposal.md` for motivation and the delta specs for observable requirements.

## Goals / Non-Goals

**Goals:**

- Keep the current endpoint and ownership contract while making context assembly explicit and bounded.
- Represent deterministic runtime facts separately from persisted conversation content.
- Give both provider adapters one typed stream/result/error contract with metadata.
- Make lifecycle transitions durable, idempotent, and observable across success, failure, and disconnect.
- Add bounded retry behavior without duplicating retry loops in provider adapters.

**Non-Goals:**

- Token-budget optimization, summarization, semantic retrieval, long-term memory, tools, or Pinus context.
- Persisting streamed partial text for later recovery.
- Cross-provider fallback or request-time provider/model routing.
- A generic plugin framework for hypothetical future context sources.

## Decisions

### Resolve runtime context once per accepted turn

Add a `RuntimeContextProvider` port returning a typed immutable value with an aware datetime, derived date, IANA timezone name, and locale. The standalone adapter uses configured defaults and a clock dependency so tests are deterministic. Resolve it after the accepted user turn is persisted and before prompt construction. It is passed in memory only and never represented as a `Message` row.

Using LLM tool calling for date/time was rejected because the server already knows these deterministic facts. Reading the clock directly inside prompt formatting was rejected because it makes timezone replacement and tests harder.

### Separate history selection from prompt assembly

Introduce two focused responsibilities:

- `ConversationContextBuilder` selects eligible completed messages and applies `CHAT_HISTORY_MAX_MESSAGES` while preserving chronological order.
- `PromptBuilder` assembles neutral chat messages in four sections: system instruction, runtime-context instruction, selected history, current user message.

The repository will return historical messages separately from the accepted current user turn so that it cannot accidentally appear twice. Selection should happen in the database query with a deterministic descending limit followed by in-memory reversal, avoiding loading unlimited history.

A generic chain of context plugins was rejected for now; future Pinus/RAG/memory sources can extend a typed prompt input or composition boundary when they have concrete requirements.

### Upgrade the provider port from bare strings to typed stream items

Define neutral stream items for text deltas and a successful terminal result carrying provider, model, and optional input/output token usage. Adapters translate SDK events into these types and must emit exactly one terminal result only after provider completion. Chat orchestration remains responsible for measuring end-to-end latency and persisting metadata.

Embedding provider metadata in every delta was rejected as redundant. Returning raw SDK completion objects was rejected because it leaks vendor coupling.

### Normalize errors with a small application hierarchy

Use a base `LLMProviderError` with stable subclasses/codes for rate limit, timeout, unavailable, invalid request, authentication/configuration, and generic upstream failure. Adapters log redacted provider/error-type/status metadata and raise normalized errors; `ChatService` maps only stable codes into SSE.

Raw response bodies, exception messages, prompts, and secrets remain outside client payloads and normal logs.

### Apply retries around generation startup only

Use a provider-neutral retry policy/decorator around opening a provider stream. Retry only normalized transient errors configured as safe, with a finite attempt count and bounded delay. Once any text delta has been emitted, do not restart generation because replay could duplicate user-visible output and produce conflicting completions.

Authentication, configuration, invalid-request, cancellation, and post-delta failures are never retried. Uncontrolled SDK retries should be disabled or aligned so total attempts remain predictable.

### Use explicit durable lifecycle states

Migrate assistant statuses to `pending`, `streaming`, `completed`, `failed`, and `cancelled`. Preparing a turn atomically writes the completed user message and pending assistant row. Immediately before provider work, transition pending to streaming. Terminal updates use compare-and-set predicates and are idempotent. No partial delta content is written; only the final joined response is stored on successful completion.

Existing `in_progress` rows migrate to `streaming`; existing `interrupted` rows migrate to `cancelled`. Stale recovery changes old streaming rows to cancelled. Existing completed/failed states remain unchanged.

### Store generation metadata on the assistant message

Add nullable provider, model, latency milliseconds, input tokens, and output tokens to assistant messages. This is the smallest schema that keeps metadata aligned with the existing one-assistant-generation-per-turn model. Constraints prevent negative latency/token counts, and user messages leave these fields null.

A separate generation table was rejected because retries do not represent separate user-visible generations in this scope and per-attempt analytics are explicitly out of scope.

### Formalize SSE without changing event names

Keep `conversation`, `delta`, `completed`, and `error`. Add assistant `message_id` to delta and error events; retain the current conversation event's accepted user-message ID for backward compatibility. Completion continues to be emitted only after assistant content and metadata commit. Error payloads include IDs when known and stable safe codes only.

## Risks / Trade-offs

- [Status migration encounters active generations] → Stop API writers during migration and deterministically map existing active rows to `cancelled` or document the chosen migration mapping before deployment.
- [A message-count limit can split a user/assistant pair] → Accept simple message-count semantics for this change and document it; turn-aware or token-aware selection can follow later.
- [Locale formatting libraries add unnecessary weight] → Store a validated locale identifier and use stable ISO date/datetime text initially; locale-specific natural-language rendering can be added only when required.
- [Provider SDKs report usage differently] → Keep usage nullable and test mapping per adapter without inventing missing values.
- [Retries increase latency and cost] → Default to a conservative finite count, record total latency, and never retry after a delta is visible.
- [Client disconnect detection races with completion] → Persist completion before emitting `completed`; compare-and-set terminal transitions ensure cancellation cannot overwrite a committed completion.

## Migration Plan

1. Add nullable metadata columns and lifecycle-compatible constraints in an Alembic migration.
2. Map `in_progress` to `streaming` and `interrupted` to `cancelled`, then install the new status constraint in the same transaction where supported.
3. Deploy code that understands only the new statuses together with the migration; no public API migration is required.
4. Run upgrade, data/constraint checks, downgrade/upgrade against a disposable database, then run unit and PostgreSQL integration suites.
5. Verify Gemini manually through the unchanged endpoint and confirm completed content plus metadata in PostgreSQL.
6. Roll back code and migration together; downgrade maps `pending/streaming` to `in_progress` and `cancelled` to `interrupted`, dropping only the new nullable metadata columns.
