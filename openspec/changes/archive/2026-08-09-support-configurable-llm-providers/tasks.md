## 1. Dependencies and Configuration

- [x] 1.1 Add and pin the supported Google Gemini Python SDK dependency without adding an orchestration framework
- [x] 1.2 Add a typed, case-normalized `LLM_PROVIDER` setting supporting only `openai` and `gemini`, defaulting to OpenAI for compatibility
- [x] 1.3 Add secret-typed `GEMINI_API_KEY` and validated `GEMINI_MODEL` settings while preserving existing OpenAI settings
- [x] 1.4 Implement conditional startup validation requiring only the selected provider's non-empty key and model and clearly rejecting unsupported configurations
- [x] 1.5 Add settings tests covering both providers, missing active settings, absent inactive credentials, invalid values, aliases, and secret-safe representations

## 2. Provider-Neutral Composition

- [x] 2.1 Review and minimally extend the existing chat-model port so both adapters share one ordered-delta, completion, failure, timeout, and cancellation contract
- [x] 2.2 Add a provider factory or dependency-composition function that constructs exactly one adapter from validated settings
- [x] 2.3 Wire the chat API dependency graph through the factory while keeping `ChatService` free of provider-specific imports and branching
- [x] 2.4 Add factory and composition tests proving OpenAI and Gemini selection and fail-fast behavior for unsupported or incomplete configuration

## 3. Gemini Streaming Adapter

- [x] 3.1 Implement Gemini request translation from the existing neutral system/user/assistant message history
- [x] 3.2 Implement async Gemini streaming and normalize ordered text chunks into the existing application delta stream
- [x] 3.3 Detect empty, blocked, incomplete, or otherwise unsuccessful Gemini terminal states instead of treating transport success as generation completion
- [x] 3.4 Map Gemini authentication, quota/rate-limit, timeout, connection, cancellation, and upstream failures into sanitized existing provider errors
- [x] 3.5 Ensure Gemini streaming resources close correctly on success, provider failure, timeout, consumer cancellation, and client disconnect

## 4. OpenAI Compatibility and Stream Correctness

- [x] 4.1 Preserve the OpenAI adapter behind the shared provider contract and ensure its configuration is selected through the new factory
- [x] 4.2 Reproduce and diagnose the observed OpenAI HTTP-200 `generation_failed` stream, then handle terminal event states without falsely completing assistant messages
- [x] 4.3 Extend OpenAI adapter regression tests for current SDK event shapes, incomplete responses, empty successful responses, cleanup, and cancellation
- [x] 4.4 Verify existing OpenAI application, API/SSE, persistence, and ownership tests pass unchanged except for necessary settings fixtures

## 5. Gemini and Cross-Provider Tests

- [x] 5.1 Add mocked Gemini adapter tests for ordered deltas, successful completion, history/request mapping, and model selection
- [x] 5.2 Add mocked Gemini tests for blocked/empty/incomplete streams, authentication, quota, timeout, upstream failure, cleanup, and cancellation
- [x] 5.3 Add parameterized provider-contract tests proving both adapters expose equivalent normalized success and failure behavior
- [x] 5.4 Add API-level tests proving provider choice does not alter the chat request schema, SSE framing/order, or assistant persistence lifecycle
- [x] 5.5 Add opt-in live smoke-test instructions or tooling for OpenAI and Gemini that verifies SSE completion and the corresponding completed DB record

## 6. Environment and Documentation

- [x] 6.1 Update `.env.example` and Compose documentation with `LLM_PROVIDER`, Gemini settings, OpenAI-compatible defaults, and examples for selecting each provider
- [x] 6.2 Document that all provider credentials are server-only, inactive credentials are optional, configuration changes require restart, and invalid active settings prevent startup
- [x] 6.3 Update architecture and developer documentation with the provider factory, neutral contract, normalized failure semantics, and explicit non-goals
- [x] 6.4 Document local mock tests and real-provider smoke-test procedures without placing credentials in commands, images, logs, fixtures, or source control

## 7. Validation

- [x] 7.1 Run formatting, linting, type checks if configured, and the full unit/integration test suite
- [ ] 7.2 Build and start the Compose stack with OpenAI selected, verify real SSE completion, and confirm completed user/assistant persistence in PostgreSQL
- [x] 7.3 Start the stack with Gemini selected, verify real SSE completion, and confirm the same conversation/message persistence behavior
- [x] 7.4 Verify invalid provider, missing selected key/model, provider failure, and client interruption produce sanitized errors and never persist partial assistant output as completed
