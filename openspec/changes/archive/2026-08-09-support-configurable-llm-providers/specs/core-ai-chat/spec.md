## MODIFIED Requirements

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
