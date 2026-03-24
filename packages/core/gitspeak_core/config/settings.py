"""VeriDoc SaaS application settings.

SaaS mode uses cloud LLM providers (Groq, DeepSeek) by default.
local_only=True is only for VeriOps (self-hosted) deployments.
"""

from __future__ import annotations

import logging
import os

from pydantic import BaseModel, Field, SecretStr, model_validator

logger = logging.getLogger(__name__)

_DEFAULT_SECRET = "change-me-in-production"


class LLMSettings(BaseModel):
    """LLM provider configuration for SaaS mode."""

    local_only: bool = Field(
        default=False,
        description=(
            "When True, restrict to local Ollama models only. "
            "Default is False for VeriDoc SaaS (cloud LLM providers). "
            "Set to True only for VeriOps self-hosted deployments."
        ),
    )

    llm_backend_preference: list[str] = Field(
        default=["groq", "deepseek", "ollama"],
        description=(
            "Ordered list of LLM backends to try. "
            "SaaS default: groq -> deepseek -> ollama. "
            "VeriOps default: ollama only."
        ),
    )

    # Cloud provider API keys
    groq_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="Groq API key for cloud LLM inference",
    )
    deepseek_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="DeepSeek API key for cloud LLM inference",
    )
    openai_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="OpenAI API key (optional, for embeddings or GPT models)",
    )

    # Local provider settings
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Base URL for local Ollama instance",
    )
    ollama_model: str = Field(
        default="llama3",
        description="Default Ollama model name",
    )

    # Inference settings
    max_tokens: int = Field(default=4096, ge=1, le=32768)
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    timeout_seconds: int = Field(default=60, ge=5, le=300)

    def get_active_backend(self) -> str:
        """Return the first backend that has a valid API key configured."""
        if self.local_only:
            return "ollama"
        for backend in self.llm_backend_preference:
            if backend == "ollama":
                return "ollama"
            key = self._get_key_for_backend(backend)
            if key and key.get_secret_value():
                return backend
        return "ollama"

    def _get_key_for_backend(self, backend: str) -> SecretStr | None:
        key_map = {
            "groq": self.groq_api_key,
            "deepseek": self.deepseek_api_key,
            "openai": self.openai_api_key,
        }
        return key_map.get(backend)


class SandboxSettings(BaseModel):
    """API sandbox configuration."""

    backend: str = Field(
        default="external",
        description="Sandbox backend: external, docker, or prism",
    )
    external_base_url: str = Field(
        default="",
        description="External sandbox URL (e.g., Postman mock server)",
    )
    port: int = Field(default=4010, ge=1024, le=65535)


class AppSettings(BaseModel):
    """Top-level application settings for VeriDoc SaaS."""

    # App identity
    app_name: str = "VeriDoc"
    environment: str = Field(
        default="development",
        description="Runtime environment: development, staging, production",
    )
    debug: bool = False

    # LLM configuration
    llm: LLMSettings = Field(default_factory=LLMSettings)

    # Sandbox configuration
    sandbox: SandboxSettings = Field(default_factory=SandboxSettings)

    # Database
    database_url: str = Field(
        default="sqlite:///./veridoc.db",
        description="Database connection string",
    )

    # Auth
    secret_key: SecretStr = Field(
        default=SecretStr(_DEFAULT_SECRET),
        description="Secret key for JWT token signing",
    )
    access_token_expire_minutes: int = Field(default=60, ge=5)

    # Server
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1024, le=65535)
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    @model_validator(mode="after")
    def _guard_default_jwt_secret(self) -> "AppSettings":
        """Reject the default JWT secret in production environments.

        In staging and production, using the placeholder secret key
        is a critical security vulnerability. This validator raises
        a ValueError for production and logs a critical warning for
        staging. Development mode logs a warning for awareness.

        Returns:
            The validated AppSettings instance.

        Raises:
            ValueError: When the default secret is used in production.
        """
        secret_value = self.secret_key.get_secret_value()
        if secret_value == _DEFAULT_SECRET:
            if self.environment == "production":
                raise ValueError(
                    "FATAL: secret_key is set to the default placeholder value "
                    f"'{_DEFAULT_SECRET}'. You MUST set a unique, cryptographically "
                    "random secret before running in production. Generate one with: "
                    "python -c \"import secrets; print(secrets.token_urlsafe(64))\""
                )
            if self.environment == "staging":
                logger.critical(
                    "secret_key is the default placeholder '%s' in a staging "
                    "environment. Set a unique secret before promoting to production.",
                    _DEFAULT_SECRET,
                )
            else:
                logger.warning(
                    "secret_key is the default placeholder '%s'. "
                    "This is acceptable in development but must be changed "
                    "before deploying to staging or production.",
                    _DEFAULT_SECRET,
                )
        if self.environment in {"staging", "production"} and (
            not self.cors_origins or "*" in self.cors_origins
        ):
            raise ValueError(
                "FATAL: cors_origins must be an explicit allowlist in staging/production. "
                "Set VERIDOC_CORS_ORIGINS to comma-separated HTTPS origins."
            )
        return self


def _get_env(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value is not None:
        return value
    return default


def _get_env_int(name: str, default: int) -> int:
    raw = _get_env(name, str(default)).strip()
    try:
        return int(raw)
    except ValueError:
        logger.warning("Invalid integer for %s=%r. Using default=%s", name, raw, default)
        return default


def _parse_csv_env(value: str, fallback: list[str]) -> list[str]:
    parsed = [item.strip() for item in value.split(",") if item.strip()]
    return parsed or fallback


def get_default_settings() -> AppSettings:
    """Return application settings with environment variable overrides."""
    cors_raw = _get_env("VERIDOC_CORS_ORIGINS", "http://localhost:3000")
    cors_origins = _parse_csv_env(cors_raw, ["http://localhost:3000"])

    return AppSettings(
        environment=_get_env("VERIDOC_ENVIRONMENT", _get_env("ENVIRONMENT", "development")),
        debug=_get_env("VERIDOC_DEBUG", "false").lower() in {"1", "true", "yes", "on"},
        database_url=_get_env("VERIDOC_DATABASE_URL", "sqlite:///./veridoc.db"),
        secret_key=SecretStr(_get_env("VERIDOC_SECRET_KEY", _DEFAULT_SECRET)),
        access_token_expire_minutes=_get_env_int("VERIDOC_ACCESS_TOKEN_EXPIRE_MINUTES", 60),
        host=_get_env("VERIDOC_HOST", "0.0.0.0"),
        port=_get_env_int("VERIDOC_PORT", 8000),
        cors_origins=cors_origins,
        llm=LLMSettings(
            groq_api_key=SecretStr(_get_env("GROQ_API_KEY", "")),
            deepseek_api_key=SecretStr(_get_env("DEEPSEEK_API_KEY", "")),
            openai_api_key=SecretStr(_get_env("OPENAI_API_KEY", "")),
            ollama_base_url=_get_env("OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_model=_get_env("OLLAMA_MODEL", "llama3"),
        ),
    )


def get_veriops_settings() -> AppSettings:
    """Return settings tuned for VeriOps self-hosted deployment."""
    return AppSettings(
        llm=LLMSettings(
            local_only=True,
            llm_backend_preference=["ollama"],
        ),
    )
