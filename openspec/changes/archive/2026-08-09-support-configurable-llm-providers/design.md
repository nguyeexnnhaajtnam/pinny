## Context

Pinny already separates chat orchestration from an async streaming model port, but dependency composition and settings currently construct only the OpenAI adapter. The public chat endpoint, SSE normalization, ownership checks, and assistant lifecycle must remain provider-independent. The recent real-provider smoke test also showed that a provider can return HTTP success while the normalized generation still fails, so adapters need explicit completion-state handling and contract tests rather than relying only on transport status.

## Goals / Non-Goals

**Goals:**

- Select OpenAI or Gemini once during application composition from validated configuration.
- Keep `ChatService` dependent on a single provider-neutral streaming interface.
- Normalize provider-specific stream events into ordered text deltas and common typed failures.
- Validate only the selected provider's required secret and model while safely retaining configuration for both.
- Preserve all existing HTTP, SSE, persistence, history, cancellation, and ownership behavior.

**Non-Goals:**

- Runtime provider switching per request or conversation.
- Provider fallback, retrying through another provider, routing, or load balancing.
- A general orchestration framework or changes to conversation storage.
- Normalizing provider-specific token accounting, safety metadata, or tool calls beyond what chat currently consumes.

## Decisions

### Select the provider in dependency composition

Extend the existing chat-model port as needed, then use a small provider factory or dependency-composition function to map the validated provider enum to one concrete adapter. `ChatService` receives the resulting interface and contains no provider-name checks.

This keeps selection at the application boundary and makes unsupported values impossible after settings validation. Branching inside `ChatService` was rejected because it couples orchestration to vendors and grows with every provider.

### Use typed conditional configuration

Represent the active provider as a case-normalized enum with an explicit default chosen for backward compatibility (`openai`). Retain current OpenAI settings and add `GEMINI_API_KEY` and `GEMINI_MODEL`. A model-level validator requires a non-empty key and model only for the active provider; secrets remain secret-typed and excluded from logs and representations.

Requiring every provider's credential was rejected because it prevents a valid single-provider deployment. Deferring invalid selection until the first request was rejected because configuration errors should fail before serving traffic.

### Implement Gemini as a direct adapter

Use Google's supported Python SDK directly and translate its async streaming chunks into the same `AsyncIterator[str]` contract used by OpenAI. The adapter owns Gemini request construction, timeout/cancellation behavior, stream cleanup, empty-response/completion validation, and mapping SDK exceptions into existing sanitized provider errors.

LangChain or LangGraph is not justified for two thin SDK adapters. A shared vendor-shaped DTO was also rejected; the application already has neutral chat message and error types.

### Keep HTTP and persistence semantics above the adapters

Adapters emit only normalized deltas or normalized errors. The existing application service remains responsible for SSE events and for marking assistant messages completed, failed, or interrupted. No provider response object or error body crosses the port.

This ensures both providers inherit identical persistence behavior and prevents Gemini-specific concepts from leaking into the API.

### Test contract behavior at three layers

Settings/factory tests cover provider selection and invalid combinations. Adapter tests use mocked SDK streams to cover ordered chunks, empty/incomplete responses, provider failures, timeouts, closure, and cancellation. Existing application/API tests continue to use the neutral fake and OpenAI adapter tests remain regression coverage. A separately marked opt-in smoke test may verify each provider against real credentials without making CI depend on external APIs.

## Risks / Trade-offs

- [Provider SDKs expose different completion and error semantics] → Treat HTTP success as insufficient; explicitly validate terminal stream state and add equivalent adapter contract cases.
- [Gemini cancellation or cleanup APIs differ from OpenAI] → Encapsulate cleanup in the Gemini adapter and test cancellation at the async iterator boundary.
- [Environment variable naming can conflict with the existing `PINNY_` settings prefix] → Document the exact accepted names and aliases, and test loading them from environment and Compose.
- [Changing the default could break existing deployments] → Default to OpenAI for compatibility while requiring its existing credential/model validation when selected.
- [Mock tests can drift from real SDK event shapes] → Pin a compatible SDK range and provide opt-in live smoke-test instructions for both providers.

## Migration Plan

1. Add the Gemini dependency and settings while keeping OpenAI as the default active provider.
2. Add conditional validation, provider composition, and adapter tests before enabling Gemini in any environment.
3. Update `.env.example` and documentation with separate OpenAI and Gemini examples and secret-handling guidance.
4. Deploy existing environments unchanged as OpenAI, then opt a development environment into Gemini and run the common streaming/persistence smoke test.
5. Roll back by setting the provider to `openai` and restarting; no database or API migration is required.
