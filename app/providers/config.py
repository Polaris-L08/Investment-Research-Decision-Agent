"""Runtime configuration for external data providers.

The default is intentionally convenient for local development and tests, but
production must explicitly select a supported non-mock provider mode.
"""

from dataclasses import dataclass
import os

from dotenv import load_dotenv


load_dotenv()


class ProviderConfigurationError(ValueError):
    """Raised when provider runtime configuration is missing or unsafe."""


@dataclass(frozen=True)
class ProviderSettings:
    app_env: str
    mode: str

    def __post_init__(self) -> None:
        if self.app_env not in {"development", "test", "production"}:
            raise ProviderConfigurationError(
                "APP_ENV must be one of: development, test, production."
            )
        if self.mode not in {"mock", "real"}:
            raise ProviderConfigurationError(
                "PROVIDER_MODE must be either 'mock' or 'real'."
            )
        if self.app_env == "production" and self.mode == "mock":
            raise ProviderConfigurationError(
                "Mock providers are prohibited when APP_ENV=production."
            )

    @classmethod
    def from_env(cls) -> "ProviderSettings":
        app_env = os.getenv("APP_ENV", "development").strip().lower()
        if app_env not in {"development", "test", "production"}:
            raise ProviderConfigurationError(
                "APP_ENV must be one of: development, test, production."
            )

        configured_mode = os.getenv("PROVIDER_MODE")
        if configured_mode is None or not configured_mode.strip():
            if app_env == "production":
                raise ProviderConfigurationError(
                    "PROVIDER_MODE must be explicitly configured in production; "
                    "refusing to select Mock providers implicitly."
                )
            mode = "mock"
        else:
            mode = configured_mode.strip().lower()

        return cls(app_env=app_env, mode=mode)
