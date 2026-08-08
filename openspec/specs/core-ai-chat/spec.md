# Core AI Chat Specification

## Purpose

This capability lets a resolved Pinny user hold persistent, contextual AI conversations through a secure streaming API while preserving clear ownership and failure semantics.

## Requirements

### Requirement: Chat requests are validated and identity-safe
The system MUST expose `POST /api/v1/chat` with a required non-empty `message` and an optional `conversation_id`, and MUST NOT accept a user identity from the public request payload.

#### Scenario: Valid new-conversation request
- **WHEN** the resolved current user submits a non-empty message without a conversation identifier
- **THEN** the system MUST accept the request and create a conversation owned by that resolved user

#### Scenario: Valid follow-up request
- **WHEN** the resolved current user submits a non-empty message with a valid conversation identifier they own
- **THEN** the system MUST accept the message as a follow-up in that conversation

#### Scenario: Invalid request is rejected
- **WHEN** a request has an empty or invalid message or a malformed conversation identifier
- **THEN** the system MUST reject it with a structured validation error without creating a conversation or message

#### Scenario: Request attempts to supply user identity
- **WHEN** a request includes `user_id` or another unsupported public field
- **THEN** the system MUST reject the request and MUST NOT use that value for ownership

### Requirement: Current user identity is resolved behind a replaceable boundary
The system MUST resolve a required current user identifier through a request identity abstraction before invoking chat behavior, and the chat application behavior MUST depend only on the resolved identifier rather than its source.

#### Scenario: Development identity is resolved
- **WHEN** the service runs in the documented Phase 1 development mode with a configured development user identifier
- **THEN** the identity abstraction MUST return that non-empty identifier as the current user

#### Scenario: Development identity is missing
- **WHEN** Phase 1 development identity is enabled without a valid configured user identifier
- **THEN** the system MUST fail clearly rather than create a conversation with a null or fabricated owner

#### Scenario: Development identity is used in production
- **WHEN** the configuration-backed development identity mechanism is selected for a production environment
- **THEN** the system MUST reject the unsafe configuration as non-production behavior

### Requirement: Conversations and messages are durably persisted
The system MUST persist every conversation with a non-null owner and timestamps, and MUST persist accepted user messages and successfully completed assistant messages in PostgreSQL.

#### Scenario: New conversation is persisted
- **WHEN** a valid chat request omits `conversation_id`
- **THEN** the system MUST persist a new conversation owned by the resolved current user before generation begins

#### Scenario: User message is persisted
- **WHEN** a chat request is accepted for a new or existing conversation
- **THEN** the system MUST persist the user message in that conversation before invoking the language model

#### Scenario: Successful assistant message is persisted
- **WHEN** generation completes successfully
- **THEN** the system MUST persist exactly one completed assistant message containing the full generated response and update the conversation timestamp

#### Scenario: Persistence fails before generation
- **WHEN** the conversation or user message cannot be persisted
- **THEN** the system MUST NOT invoke the language model and MUST return a structured service error

### Requirement: Conversation access is owner-scoped
The system MUST permit conversation history and follow-up access only when the persisted conversation owner matches the resolved current user.

#### Scenario: Owner accesses conversation
- **WHEN** the resolved current user references a conversation they own
- **THEN** the system MUST load and use that conversation

#### Scenario: Different user references conversation
- **WHEN** the resolved current user references a conversation owned by another user
- **THEN** the system MUST deny access without disclosing the other user's conversation content and MUST NOT persist the submitted message

#### Scenario: Conversation does not exist
- **WHEN** the resolved current user references an unknown conversation identifier
- **THEN** the system MUST return a structured not-found error and MUST NOT persist the submitted message

### Requirement: Follow-up generations use conversation context
The system MUST send a basic Pinny system instruction and the ordered persisted conversation history, including the accepted current user message, to the configured language model provider.

#### Scenario: First message is generated with system context
- **WHEN** a new conversation starts generation
- **THEN** the model input MUST contain the Pinny system instruction followed by the first user message

#### Scenario: Follow-up uses completed history
- **WHEN** generation starts for an existing conversation
- **THEN** the model input MUST preserve the chronological roles and content of its completed user and assistant messages followed by the current user message

#### Scenario: Unsuccessful assistant output is excluded from history
- **WHEN** a previous generation failed or was interrupted
- **THEN** incomplete assistant output MUST NOT be supplied as a completed historical assistant message

### Requirement: Assistant output is streamed through SSE
The system MUST return assistant generation through a standards-compliant Server-Sent Events stream that identifies the conversation and distinguishes content, completion, and error events.

#### Scenario: Successful streaming response
- **WHEN** the language model yields response content successfully
- **THEN** the stream MUST identify the conversation, emit ordered content deltas, and finish with one completion event

#### Scenario: Existing conversation is streamed
- **WHEN** a valid follow-up request supplies an owned conversation identifier
- **THEN** every event MUST relate to that same conversation identifier

#### Scenario: Stream framing is valid
- **WHEN** the server emits an event
- **THEN** it MUST use valid SSE framing and JSON event data so clients can parse event type and payload boundaries

### Requirement: Generation failures and interruptions are explicit
The system MUST distinguish successful completion from provider failure and client interruption and MUST NOT persist partial output as a completed assistant message.

#### Scenario: Provider fails before streaming content
- **WHEN** the language model provider fails before any assistant content is emitted
- **THEN** the system MUST return or emit a structured generation error and MUST NOT persist an assistant message as completed

#### Scenario: Provider fails after partial content
- **WHEN** the language model provider fails after one or more content deltas
- **THEN** the stream MUST end with an error event rather than a completion event and MUST NOT persist the partial assistant output as completed

#### Scenario: Client disconnects during generation
- **WHEN** the client disconnects before generation completes
- **THEN** the system MUST cancel or close provider streaming work, MUST NOT emit a completion event, and MUST NOT persist partial assistant output as completed

### Requirement: Language model credentials and errors are protected
The system MUST load credentials for the configured language-model provider from server-side configuration, MUST keep provider integration replaceable, and MUST prevent credentials and sensitive provider details from reaching clients or plaintext logs.

#### Scenario: Credential is configured
- **WHEN** the service starts with valid credential and model configuration for the selected supported provider
- **THEN** that provider MUST be able to authenticate without exposing its credential through the chat API

#### Scenario: Credential is missing
- **WHEN** chat service startup is attempted without the credential required by the selected provider
- **THEN** the system MUST fail clearly during configuration validation or startup with sanitized diagnostics

#### Scenario: Provider returns a sensitive error
- **WHEN** the selected provider returns an error containing credentials or internal details
- **THEN** the system MUST log only redacted diagnostic context and return a stable sanitized API or SSE error
