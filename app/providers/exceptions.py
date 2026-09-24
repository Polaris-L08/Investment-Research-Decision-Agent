class TransientProviderError(Exception):
    """Temporary provider failure that may succeed when retried."""