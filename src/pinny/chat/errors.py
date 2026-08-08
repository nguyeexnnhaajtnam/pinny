class ChatError(Exception):
    code = "chat_error"


class ConversationNotFoundError(ChatError):
    code = "conversation_not_found"


class GenerationInProgressError(ChatError):
    code = "generation_in_progress"


class PersistenceError(ChatError):
    code = "persistence_error"


class ProviderConfigurationError(ChatError):
    code = "provider_not_configured"


class ProviderError(ChatError):
    code = "provider_error"


class ProviderTimeoutError(ProviderError):
    code = "provider_timeout"


class ContextLimitError(ChatError):
    code = "context_limit_exceeded"
