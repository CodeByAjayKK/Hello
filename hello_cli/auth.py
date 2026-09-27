from __future__ import annotations

import getpass
import os
from typing import Final

import keyring
import typer

SERVICE_NAME: Final[str] = "hello_cli"
DEFAULT_PROVIDER: Final[str] = "openai"
SUPPORTED_PROVIDERS: Final[tuple[str, ...]] = (
    "openai",
    "anthropic",
    "google",
    "groq",
)


def normalize_provider(provider: str | None) -> str:
    """Normalize and validate the LLM provider name."""
    normalized = (provider or os.getenv("HELLO_LLM_PROVIDER") or DEFAULT_PROVIDER).lower().strip()
    if normalized not in SUPPORTED_PROVIDERS:
        supported = ", ".join(SUPPORTED_PROVIDERS)
        raise ValueError(f"Unsupported provider '{provider}'. Supported providers: {supported}")
    return normalized


def provider_key(provider: str | None) -> str:
    """Generate the OS keyring key for a provider-specific secret."""
    return f"{normalize_provider(provider)}_api_key"


def set_provider(provider: str) -> None:
    """Persist the selected provider in the OS keychain."""
    keyring.set_password(SERVICE_NAME, "llm_provider", normalize_provider(provider))


def get_provider() -> str:
    """Return the currently selected provider."""
    provider = keyring.get_password(SERVICE_NAME, "llm_provider") or os.getenv("HELLO_LLM_PROVIDER")
    if not provider:
        return DEFAULT_PROVIDER
    return normalize_provider(provider)


def _selected_provider(provider: str | None = None) -> str:
    """Resolve the active provider, preferring the explicit argument then stored state."""
    if provider:
        return normalize_provider(provider)
    return get_provider()


def set_api_key(api_key: str, provider: str | None = None) -> None:
    """Persist the API key for a provider in the OS keychain."""
    if not api_key or not api_key.strip():
        raise ValueError("API key cannot be blank.")

    selected_provider = normalize_provider(provider)
    keyring.set_password(SERVICE_NAME, provider_key(selected_provider), api_key.strip())
    set_provider(selected_provider)


def get_api_key(provider: str | None = None) -> str:
    """Fetch the stored API key for a provider from the OS keychain."""
    selected_provider = _selected_provider(provider)
    api_key = keyring.get_password(SERVICE_NAME, provider_key(selected_provider))
    if api_key:
        return api_key

    env_var_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        "groq": "GROQ_API_KEY",
    }
    env_var_name = env_var_map[selected_provider]
    api_key = os.getenv(env_var_name)
    if api_key:
        return api_key

    raise RuntimeError(
        f"No API key is configured for provider '{selected_provider}'. Run 'hello auth --provider {selected_provider}' first."
    )


def configure_auth(provider: str | None = None) -> None:
    """Interactively capture and store the API key without printing it."""
    selected_provider = normalize_provider(provider)
    typer.echo(f"Configure your LLM API key for {selected_provider}.")
    api_key = getpass.getpass(f"Enter your {selected_provider} API key: ").strip()

    if not api_key:
        raise typer.BadParameter("API key cannot be empty.")

    try:
        set_api_key(api_key, provider=selected_provider)
    except Exception as exc:  # pragma: no cover - platform/security edge case
        typer.secho(f"Failed to store the API key securely: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    typer.secho(f"API key saved securely for provider '{selected_provider}'.", fg=typer.colors.GREEN)
