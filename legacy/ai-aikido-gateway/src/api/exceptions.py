"""
Custom exceptions for the AI Aikido Gateway API

Provides specific exception types for better error handling and model capability detection.
"""


class ModelNotSupportedException(Exception):
    """
    Raised when a requested model is not supported by the gateway.

    This exception is used to signal that a model exists but isn't implemented yet,
    allowing the API to return proper error messages and capabilities information.
    """

    def __init__(self, model: str, reason: str = None):
        self.model = model
        self.reason = reason or f"Model '{model}' is not currently supported"
        super().__init__(self.reason)


class ProviderNotConfiguredException(Exception):
    """
    Raised when a provider's API credentials are not configured.

    This indicates that the gateway could support the model, but the necessary
    API keys or configuration are missing.
    """

    def __init__(self, provider: str, env_var: str = None):
        self.provider = provider
        self.env_var = env_var
        message = f"Provider '{provider}' is not configured"
        if env_var:
            message += f" (missing {env_var})"
        super().__init__(message)


class ImplementationMissingException(Exception):
    """
    Raised when a model/provider integration is planned but not yet implemented.

    This is used for features that are roadmapped but not yet available,
    helping distinguish between unsupported models and not-yet-implemented ones.
    """

    def __init__(self, model: str, provider: str, reason: str = None):
        self.model = model
        self.provider = provider
        self.reason = reason or f"Integration for {provider} models is not yet implemented"
        super().__init__(self.reason)
