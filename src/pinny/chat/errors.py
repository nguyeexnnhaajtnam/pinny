class ChatError(Exception):
    code = "chat_error"


class ConversationNotFoundError(ChatError):
    code = "conversation_not_found"


class GenerationInProgressError(ChatError):
    code = "generation_in_progress"


class PersistenceError(ChatError):
    code = "persistence_error"


class LLMProviderError(ChatError):
    retryable = False


class ProviderConfigurationError(LLMProviderError):
    code = "provider_not_configured"


class ProviderError(LLMProviderError):
    code = "provider_error"


class ProviderTimeoutError(ProviderError):
    code = "provider_timeout"
    retryable = True


class ProviderRateLimitError(ProviderError):
    code = "provider_rate_limit"
    retryable = True


class ProviderUnavailableError(ProviderError):
    code = "provider_unavailable"
    retryable = True


class ProviderInvalidRequestError(ProviderError):
    code = "provider_invalid_request"


class ProviderAuthenticationError(ProviderError):
    code = "provider_authentication_failed"


class ContextLimitError(ChatError):
    code = "context_limit_exceeded"
