"""VeriDoc SaaS application settings.

SaaS mode uses cloud LLM providers (Groq, DeepSeek) by default.
local_only=True is only for VeriOps (self-hosted) deployments.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, SecretStr


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
        default=SecretStr("change-me-in-production"),
        description="Secret key for JWT token signing",
    )
    access_token_expire_minutes: int = Field(default=60, ge=5)

    # Server
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1024, le=65535)


def get_default_settings() -> AppSettings:
    """Return default application settings."""
    return AppSettings()


def get_veriops_settings() -> AppSettings:
    """Return settings tuned for VeriOps self-hosted deployment."""
    return AppSettings(
        llm=LLMSettings(
            local_only=True,
            llm_backend_preference=["ollama"],
        ),
    )
