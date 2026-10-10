"""Runtime provider bundle access and explicit dependency injection."""

from app.providers.factory import ProviderBundle, create_provider_bundle


_provider_bundle = create_provider_bundle()


def get_provider_bundle() -> ProviderBundle:
    """Return the currently configured provider dependencies."""
    return _provider_bundle


def configure_provider_bundle(bundle: ProviderBundle) -> None:
    """Replace runtime providers, primarily during application assembly/tests."""
    if not isinstance(bundle, ProviderBundle):
        raise TypeError("bundle must be a ProviderBundle instance")
    global _provider_bundle
    _provider_bundle = bundle


def reset_provider_bundle() -> None:
    """Rebuild providers from the current environment configuration."""
    global _provider_bundle
    _provider_bundle = create_provider_bundle()
