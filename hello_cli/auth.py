from __future__ import annotations

import getpass
from typing import Final

import keyring
import typer

SERVICE_NAME: Final[str] = "hello_cli"
KEY_NAME: Final[str] = "llm_api_key"


def set_api_key(api_key: str) -> None:
    """Persist the API key in the OS keychain."""
    if not api_key or not api_key.strip():
        raise ValueError("API key cannot be blank.")

    keyring.set_password(SERVICE_NAME, KEY_NAME, api_key.strip())


def get_api_key() -> str:
    """Fetch the stored API key from the OS keychain."""
    api_key = keyring.get_password(SERVICE_NAME, KEY_NAME)
    if not api_key:
        raise RuntimeError("No API key is configured. Run 'hello auth' first.")
    return api_key


def configure_auth() -> None:
    """Interactively capture and store the API key without printing it."""
    typer.echo("Configure your LLM API key for hello.")
    api_key = getpass.getpass("Enter your LLM API key: ").strip()

    if not api_key:
        raise typer.BadParameter("API key cannot be empty.")

    try:
        set_api_key(api_key)
    except Exception as exc:  # pragma: no cover - platform/security edge case
        typer.secho(f"Failed to store the API key securely: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    typer.secho("API key saved securely to your OS credential manager.", fg=typer.colors.GREEN)
