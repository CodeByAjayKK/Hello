"""CLI entry point for the hello command."""

from __future__ import annotations

import sys

import typer
from rich.console import Console
from rich.panel import Panel

from .agent import run_agent
from .auth import configure_auth, get_api_key
from .executor import execute_command
from .history import log_interaction, show_history

app = typer.Typer(
    help="hiwiz — your AI CLI friend for safe shell command generation.",
    add_completion=False,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)


@app.callback(invoke_without_command=True)
def callback(ctx: typer.Context) -> None:
    """Handle either a subcommand or a free-form user prompt."""
    if ctx.invoked_subcommand is not None:
        return

    if ctx.args:
        joined_prompt = " ".join(ctx.args)
        if joined_prompt in {"help", "auth", "history"}:
            return
        raise typer.Exit(run_prompt(joined_prompt))

    help_command()
    raise typer.Exit(0)


@app.command("help")
def help_command() -> None:
    """Show usage information and what hello does."""
    console = Console()
    console.print(
        Panel.fit(
            "[bold cyan]hiwiz[/bold cyan] converts natural-language requests into safe shell commands.\n\n"
            "Examples:\n"
            "  hiwiz list files in this directory\n"
            "  hiwiz show git status\n"
            "  hiwiz commit the message 'initial commit'\n\n"
            "Commands:\n"
            "  hiwiz auth      Securely configure your LLM API key\n"
            "  hiwiz history   View recent command history\n"
            "  hiwiz help      Show this overview\n\n"
            "Safety:\n"
            "  Commands are validated before execution and require confirmation.",
            border_style="cyan",
        )
    )


@app.command("auth")
def auth_command(
    provider: str = typer.Option(
        "openai",
        "--provider",
        help="LLM provider to configure. Supported: openai, anthropic, google, groq.",
    ),
) -> None:
    """Set or update the API key used by the LLM agent."""
    configure_auth(provider=provider)


@app.command("history")
def history_command() -> None:
    """Display the most recent command history."""
    show_history()


def run_prompt(user_prompt: str) -> int:
    """Execute the LangGraph workflow for a free-form user request."""
    console = Console()

    try:
        get_api_key()
    except RuntimeError:
        console.print(
            Panel.fit(
                "[bold red]No API key is configured.[/bold red]\nRun [cyan]hiwiz auth[/cyan] to save your LLM API key securely.",
                border_style="red",
            )
        )
        return 1

    try:
        state = run_agent(user_prompt)
    except Exception as exc:  # pragma: no cover - runtime integration path
        console.print(f"[bold red]Agent execution failed:[/bold red] {exc}")
        return 1

    generated_command = state.get("generated_command", "").strip()
    if not generated_command:
        console.print("[bold red]The agent did not generate a command.[/bold red]")
        return 1

    if not state.get("is_safe"):
        console.print("[bold red]Blocked by security policy.[/bold red]")
        log_interaction(user_prompt, generated_command, False)
        return 1

    if state.get("execution_result") == "Command execution cancelled by user.":
        console.print("[yellow]Execution cancelled by the user.[/yellow]")
        log_interaction(user_prompt, generated_command, False)
        return 0

    result = execute_command(generated_command)
    if result.success:
        console.print(
            Panel.fit(
                f"[green]Command succeeded[/green]\n\n[cyan]{generated_command}[/cyan]\n\n"
                f"{result.stdout or 'No output.'}",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel.fit(
                f"[red]Command failed (exit {result.returncode})[/red]\n\n"
                f"[cyan]{generated_command}[/cyan]\n\n"
                f"{result.stderr or result.stdout or 'No output.'}",
                border_style="red",
            )
        )

    log_interaction(user_prompt, generated_command, result.success)
    if not result.success:
        return result.returncode

    return 0


def main() -> int:
    """Dispatch either a Typer subcommand or a free-form natural-language prompt."""
    argv = sys.argv[1:]

    if not argv:
        help_command()
        return 0

    if argv[0] in {"help", "auth", "history"} or argv[0] in {"--help", "-h"}:
        app()
        return 0

    user_prompt = " ".join(argv).strip()
    if not user_prompt:
        help_command()
        return 0

    return run_prompt(user_prompt)


if __name__ == "__main__":
    raise SystemExit(main())
