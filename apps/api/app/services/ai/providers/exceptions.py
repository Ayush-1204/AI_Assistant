class ProviderError(Exception):
    """Base exception for all provider issues."""
    pass

class ProviderTransientError(ProviderError):
    """Temporary errors (Rate Limits, Timeouts) that should be retried."""
    pass

class ProviderAuthenticationError(ProviderError):
    """Authentication failures that should NOT be retried."""
    pass

class ProviderConfigurationError(ProviderError):
    """Configuration failures that should NOT be retried."""
    pass

class AllProvidersFailedError(ProviderError):
    """Raised when the router exhausts its fallback chain completely."""
    pass
