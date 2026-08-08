## Why

Pinny's chat pipeline currently has a replaceable model boundary but deploys only with OpenAI-specific configuration. Supporting Google Gemini through the same boundary lets operators choose either provider without changing the public chat contract, persistence lifecycle, or SSE semantics.

## What Changes

- Preserve the existing OpenAI adapter and add a Google Gemini streaming adapter.
- Select exactly one active LLM provider through validated server-side configuration supporting `openai` and `gemini`.
- Add server-only Gemini API key and model settings while retaining OpenAI settings.
- Keep provider construction outside `ChatService` and normalize both providers to the existing application-level streaming contract.
- Fail clearly during configuration validation or startup for unsupported providers or missing active-provider credentials.
- Add provider-selection, Gemini streaming, error, and OpenAI regression tests.
- Update environment templates and developer documentation for both providers.
- Explicitly exclude fallback, automatic routing, load balancing, LangChain, LangGraph, RAG, embeddings, Pinus tools, and file processing.

## Capabilities

### New Capabilities

- `llm-provider-configuration`: Defines validated provider selection, provider-specific server credentials, construction behind a neutral boundary, and equivalent normalized streaming behavior for OpenAI and Gemini.

### Modified Capabilities

- `core-ai-chat`: Generalizes the existing OpenAI-specific credential requirement so the unchanged chat and SSE contract works with whichever supported provider is configured.

## Impact

- Affects application dependency composition, LLM adapters, typed settings, environment templates, tests, and developer documentation.
- Adds the official Google Gemini SDK or an equivalent direct provider client; no orchestration framework is introduced.
- Does not change `POST /api/v1/chat`, its request shape, SSE event schema, conversation ownership, or PostgreSQL models and persistence rules.
- Existing OpenAI deployments remain supported, subject to explicit valid provider configuration.
