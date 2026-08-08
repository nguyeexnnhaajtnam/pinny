## Purpose

This capability lets Pinny operators select a supported language-model provider through secure, validated server configuration while presenting one stable streaming contract to chat behavior.

## ADDED Requirements

### Requirement: Active LLM provider is selected through configuration
The system MUST select exactly one active language-model provider from server-side configuration and MUST support the values `openai` and `gemini`.

#### Scenario: OpenAI is selected
- **WHEN** `LLM_PROVIDER` is configured as `openai` with valid active-provider settings
- **THEN** the system MUST construct and use the OpenAI provider for chat generation

#### Scenario: Gemini is selected
- **WHEN** `LLM_PROVIDER` is configured as `gemini` with valid active-provider settings
- **THEN** the system MUST construct and use the Gemini provider for chat generation

#### Scenario: Provider is unsupported
- **WHEN** `LLM_PROVIDER` contains an unsupported value
- **THEN** configuration validation or application startup MUST fail with a clear sanitized error

### Requirement: Active-provider configuration is validated securely
The system MUST require the API credential and model configuration needed by the selected provider, MUST keep credentials server-side, and MUST NOT require credentials for an inactive provider.

#### Scenario: Active provider credential is missing
- **WHEN** the selected provider has no non-empty API key configured
- **THEN** configuration validation or application startup MUST fail before accepting chat traffic

#### Scenario: Active provider model is missing
- **WHEN** the selected provider has no valid model configured
- **THEN** configuration validation or application startup MUST fail clearly

#### Scenario: Inactive provider credential is absent
- **WHEN** the selected provider is valid and fully configured but the inactive provider has no credential
- **THEN** the service MUST start without requiring the inactive provider credential

#### Scenario: Configuration is exposed externally
- **WHEN** clients receive API responses or operators inspect ordinary application logs
- **THEN** provider API credentials MUST NOT appear in responses or plaintext logs

### Requirement: Supported providers expose equivalent application streaming behavior
Each supported provider MUST expose ordered text deltas, successful completion, failure, timeout, and cancellation through the same provider-neutral application contract.

#### Scenario: Gemini streams successfully
- **WHEN** Gemini emits a successful streaming response
- **THEN** its ordered text chunks MUST be normalized as application deltas followed by successful completion

#### Scenario: OpenAI streams successfully
- **WHEN** OpenAI emits a successful streaming response
- **THEN** its ordered text chunks MUST continue to be normalized as application deltas followed by successful completion

#### Scenario: Selected provider fails during streaming
- **WHEN** the selected provider fails, times out, or is cancelled during generation
- **THEN** the provider boundary MUST report the equivalent normalized outcome required by chat failure and interruption handling

### Requirement: Provider selection does not alter the chat contract
Changing the configured provider MUST NOT change the public chat request schema, SSE event schema, conversation ownership rules, or persistence lifecycle.

#### Scenario: Provider is changed between deployments
- **WHEN** an operator changes the valid active provider and restarts the service
- **THEN** clients MUST continue using the same chat endpoint and SSE event contract

#### Scenario: Chat application invokes generation
- **WHEN** chat generation begins with either supported provider selected
- **THEN** application orchestration MUST invoke the provider-neutral contract without provider-specific branching
