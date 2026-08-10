## ADDED Requirements

### Requirement: Runtime context is deterministic and non-persistent
The system MUST resolve the current date, current datetime, timezone, and locale through a provider-neutral runtime-context boundary and MUST include that context in model input without persisting it as a user or assistant message.

#### Scenario: Standalone runtime context is resolved
- **WHEN** chat generation begins in standalone development
- **THEN** the model input MUST contain the server-resolved date and datetime expressed using the configured timezone and locale defaults

#### Scenario: Runtime context is not persisted
- **WHEN** a chat turn completes or fails
- **THEN** no runtime-context entry MUST appear as a conversation message in PostgreSQL

#### Scenario: Runtime context configuration is invalid
- **WHEN** the configured timezone or locale is invalid
- **THEN** configuration validation or application startup MUST fail clearly without accepting chat traffic

### Requirement: Prompt input has explicit provider-neutral sections
The system MUST construct model input from distinct Pinny system instructions, runtime context, bounded conversation history, and the accepted current user message without provider-specific prompt logic in chat orchestration.

#### Scenario: First-turn prompt is constructed
- **WHEN** a new conversation starts generation
- **THEN** model input MUST contain system instructions, runtime context, and the current user message in their defined order with no historical messages

#### Scenario: Follow-up prompt is constructed
- **WHEN** an existing conversation starts generation
- **THEN** model input MUST contain system instructions, runtime context, selected chronological history, and the current user message in their defined order

#### Scenario: Future context source is absent
- **WHEN** no optional external context source is configured
- **THEN** prompt construction MUST succeed without fabricating Pinus, retrieval, or memory context

### Requirement: LLM generation metadata is recorded
The system MUST record the selected provider, model, latency, terminal generation status, and provider-reported input and output token usage when available without storing credentials or raw provider responses.

#### Scenario: Provider reports complete usage
- **WHEN** generation terminates and the provider supplies input and output token counts
- **THEN** the system MUST associate those counts and the provider, model, latency, and terminal status with the assistant generation

#### Scenario: Provider omits usage
- **WHEN** generation terminates without token usage from the provider
- **THEN** the system MUST record the available metadata and leave unavailable usage values unset rather than invent values

#### Scenario: Generation fails
- **WHEN** generation fails or is cancelled
- **THEN** the system MUST record the corresponding terminal generation status and available non-sensitive metadata

## MODIFIED Requirements

### Requirement: Conversations and messages are durably persisted
The system MUST persist every conversation with a non-null owner and timestamps, MUST persist accepted user messages, and MUST persist an assistant generation record whose state distinguishes `pending`, `streaming`, `completed`, `failed`, and `cancelled` outcomes.

#### Scenario: New conversation is persisted
- **WHEN** a valid chat request omits `conversation_id`
- **THEN** the system MUST persist a new conversation owned by the resolved current user before generation begins

#### Scenario: User message and pending generation are persisted
- **WHEN** a chat request is accepted for a new or existing conversation
- **THEN** the system MUST atomically persist the completed user message and a pending assistant generation before invoking the language model

#### Scenario: User message is persisted
- **WHEN** a chat request is accepted for a new or existing conversation
- **THEN** the system MUST persist the user message in that conversation before invoking the language model

#### Scenario: Generation starts streaming
- **WHEN** provider generation work begins
- **THEN** the assistant generation MUST transition from `pending` to `streaming`

#### Scenario: Successful assistant message is persisted
- **WHEN** generation completes successfully
- **THEN** the system MUST persist exactly one completed assistant message containing the full generated response, mark the generation `completed`, and update the conversation timestamp before emitting completion

#### Scenario: Persistence fails before generation
- **WHEN** the conversation, user message, or pending generation cannot be persisted
- **THEN** the system MUST NOT invoke the language model and MUST return a structured service error

### Requirement: Follow-up generations use conversation context
The system MUST apply a configurable provider-neutral recent-message policy to completed persisted history, preserve chronological order, and place the accepted current user message after the selected history in model input.

#### Scenario: First message is generated with system context
- **WHEN** a new conversation starts generation
- **THEN** the model input MUST contain the Pinny system instruction and runtime context followed by the first user message

#### Scenario: Follow-up uses completed history
- **WHEN** generation starts for an existing conversation
- **THEN** the model input MUST preserve the chronological roles and content of the selected completed user and assistant messages followed by the current user message

#### Scenario: History is within the configured limit
- **WHEN** the number of eligible historical messages does not exceed the configured maximum
- **THEN** all eligible messages MUST be supplied in chronological order

#### Scenario: History exceeds the configured limit
- **WHEN** eligible historical messages exceed the configured maximum
- **THEN** only the most recent configured number of eligible messages MUST be supplied while preserving chronological order among them

#### Scenario: Unsuccessful assistant output is excluded from history
- **WHEN** a previous assistant generation is pending, streaming, failed, or cancelled
- **THEN** its incomplete output MUST NOT be supplied as completed historical context

#### Scenario: Current user message follows history
- **WHEN** generation starts for a new or existing conversation
- **THEN** the accepted current user message MUST appear exactly once after the selected historical messages

### Requirement: Assistant output is streamed through SSE
The system MUST expose only the provider-neutral SSE events `conversation`, `delta`, `completed`, and `error`, with JSON payloads that consistently identify the conversation and relevant assistant generation without leaking provider response structures.

#### Scenario: Successful streaming response
- **WHEN** the language model yields response content successfully
- **THEN** the stream MUST identify the conversation, emit ordered `delta` events, and finish with exactly one `completed` event

#### Scenario: Existing conversation is streamed
- **WHEN** a valid follow-up request supplies an owned conversation identifier
- **THEN** every event MUST relate to that same conversation identifier

#### Scenario: Stream framing is valid
- **WHEN** the server emits an event
- **THEN** it MUST use valid SSE framing and JSON event data so clients can parse event type and payload boundaries

#### Scenario: Conversation event is emitted
- **WHEN** streaming begins for an accepted chat turn
- **THEN** one `conversation` event MUST identify the conversation and accepted user message

#### Scenario: Delta event is emitted
- **WHEN** normalized assistant text is produced
- **THEN** each ordered `delta` event MUST include the conversation identifier, assistant message identifier, and text content

#### Scenario: Completion event is emitted
- **WHEN** the full assistant response and generation metadata have been persisted successfully
- **THEN** exactly one `completed` event MUST include the conversation and completed assistant message identifiers

#### Scenario: Error event is emitted
- **WHEN** generation fails after streaming has begun
- **THEN** one terminal `error` event MUST include available conversation and assistant message identifiers, a normalized error code, and a safe user-facing message, and no completion event may follow

#### Scenario: Provider payload remains internal
- **WHEN** OpenAI or Gemini emits provider-specific stream data
- **THEN** no provider-specific type, raw payload, or sensitive detail MUST appear in the public SSE events

### Requirement: Generation failures and interruptions are explicit
The system MUST distinguish successful completion, provider failure, and client cancellation, MUST close active provider work, and MUST never persist a partial assistant response as completed.

#### Scenario: Provider fails before streaming content
- **WHEN** the language model provider fails before any assistant content is emitted
- **THEN** the assistant generation MUST become `failed`, no partial content may be marked completed, and the client MUST receive a normalized failure outcome

#### Scenario: Provider fails after partial content
- **WHEN** the language model provider fails after one or more deltas
- **THEN** the generation MUST become `failed`, the stream MUST terminate with an error event, and partial output MUST NOT be persisted as a completed assistant message

#### Scenario: Client disconnects during generation
- **WHEN** the client disconnects before generation completes
- **THEN** provider streaming work MUST be cancelled or closed, the generation MUST become `cancelled`, no completion event may be emitted, and partial output MUST NOT be marked completed

#### Scenario: Terminal cleanup is repeated
- **WHEN** failure or cancellation cleanup runs more than once for the same generation
- **THEN** the terminal transition MUST remain idempotent and MUST NOT overwrite a completed generation
