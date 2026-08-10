## ADDED Requirements

### Requirement: Provider failures are normalized before application handling
Each supported provider MUST translate authentication, rate-limit, timeout, unavailability, invalid-request, and unexpected provider failures into stable provider-neutral application errors before they reach chat orchestration.

#### Scenario: Provider rate limit occurs
- **WHEN** the selected provider reports a rate-limit or quota failure
- **THEN** the provider boundary MUST raise the normalized rate-limit error without exposing the raw provider response

#### Scenario: Provider timeout occurs
- **WHEN** the selected provider exceeds the configured timeout
- **THEN** the provider boundary MUST raise the normalized timeout error and close active streaming resources

#### Scenario: Provider is unavailable
- **WHEN** the selected provider has a transient connection or service-availability failure
- **THEN** the provider boundary MUST raise the normalized unavailable error

#### Scenario: Provider rejects the request
- **WHEN** the selected provider rejects a model request as invalid
- **THEN** the provider boundary MUST raise the normalized invalid-request error without retrying it

#### Scenario: Provider returns an unexpected failure
- **WHEN** a provider-specific failure has no more precise safe mapping
- **THEN** the provider boundary MUST raise a generic normalized provider error and log only redacted diagnostic metadata

### Requirement: Provider timeout and retry policy is bounded
The system MUST apply explicit configurable provider timeouts and MUST retry only configured transient failures up to a finite configured attempt limit.

#### Scenario: Retryable failure succeeds on retry
- **WHEN** a configured transient unavailable or rate-limit failure occurs and retry attempts remain
- **THEN** the provider operation MUST retry according to the configured bounded policy and return the successful normalized stream

#### Scenario: Retryable failures are exhausted
- **WHEN** retryable failures continue through the configured attempt limit
- **THEN** the operation MUST stop retrying and return the final normalized error

#### Scenario: Non-retryable failure occurs
- **WHEN** authentication, invalid request, invalid model configuration, or another configured non-retryable failure occurs
- **THEN** the operation MUST fail immediately without retrying

#### Scenario: Retry configuration is invalid
- **WHEN** timeout, retry count, or retry delay configuration is outside documented bounds
- **THEN** configuration validation or startup MUST fail clearly

## MODIFIED Requirements

### Requirement: Supported providers expose equivalent application streaming behavior
Each supported provider MUST expose ordered text deltas, a terminal outcome, normalized generation metadata, timeout, failure, and cancellation through the same provider-neutral application contract.

#### Scenario: Gemini streams successfully
- **WHEN** Gemini emits a successful streaming response
- **THEN** its ordered text chunks and available usage metadata MUST be normalized as application deltas and a successful terminal result

#### Scenario: OpenAI streams successfully
- **WHEN** OpenAI emits a successful streaming response
- **THEN** its ordered text chunks and available usage metadata MUST be normalized as application deltas and a successful terminal result

#### Scenario: Selected provider fails during streaming
- **WHEN** the selected provider fails or times out during generation
- **THEN** the provider boundary MUST close its stream and report the corresponding normalized application error

#### Scenario: Provider stream is cancelled
- **WHEN** the application cancels consumption before generation completes
- **THEN** the provider boundary MUST propagate cancellation and close provider streaming resources without reporting successful completion
