from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel

from .agent import run_agent
from .auth import configure_auth, get_api_key
from .executor import execute_command
from .history import log_interaction, show_history

app = typer.Typer(
    help="hello — your AI CLI friend for safe shell command generation.",
    add_completion=False,
)


@app.command("help")
def help_command() -> None:
    """Show usage information and what hello does."""
    console = Console()
    console.print(
        Panel.fit(
            "[bold cyan]hello[/bold cyan] converts natural-language requests into safe shell commands.\n\n"
            "Examples:\n"
            "  hello list files in this directory\n"
            "  hello show git status\n"
            "  hello commit the message 'initial commit'\n\n"
            "Commands:\n"
            "  hello auth      Securely configure your LLM API key\n"
            "  hello history   View recent command history\n"
            "  hello help      Show this overview\n\n"
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


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Route arbitrary text to the LangGraph agent or show help when no command is provided."""
    if ctx.invoked_subcommand is not None:
        return

    prompt = " ".join(ctx.args).strip()
    if not prompt:
        help_command()
        raise typer.Exit()

    user_prompt = prompt
    console = Console()

    try:
        get_api_key()
    except RuntimeError:
        console.print(
            Panel.fit(
                "[bold red]No API key is configured.[/bold red]\nRun [cyan]hello auth[/cyan] to save your LLM API key securely.",
                border_style="red",
            )
        )
        raise typer.Exit(code=1) from None

    try:
        state = run_agent(user_prompt)
    except Exception as exc:  # pragma: no cover - runtime integration path
        console.print(f"[bold red]Agent execution failed:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    generated_command = state.get("generated_command", "").strip()
    if not generated_command:
        console.print("[bold red]The agent did not generate a command.[/bold red]")
        raise typer.Exit(code=1)

    if not state.get("is_safe"):
        console.print("[bold red]Blocked by security policy.[/bold red]")
        log_interaction(user_prompt, generated_command, False)
        raise typer.Exit(code=1)

    if state.get("execution_result") == "Command execution cancelled by user.":
        console.print("[yellow]Execution cancelled by the user.[/yellow]")
        log_interaction(user_prompt, generated_command, False)
        raise typer.Exit(code=0)

    result = execute_command(generated_command)
    if result.success:
        console.print(Panel.fit(f"[green]Command succeeded[/green]\n\n[cyan]{generated_command}[/cyan]\n\n{result.stdout or 'No output.'}", border_style="green"))
    else:
        console.print(
            Panel.fit(
                f"[red]Command failed (exit {result.returncode})[/red]\n\n[cyan]{generated_command}[/cyan]\n\n{result.stderr or result.stdout or 'No output.'}",
                border_style="red",
            )
        )

    log_interaction(user_prompt, generated_command, result.success)
    if not result.success:
        raise typer.Exit(code=result.returncode)

    raise typer.Exit(code=0)


if __name__ == "__main__":
    app()
