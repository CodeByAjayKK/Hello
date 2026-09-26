from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass
class CommandExecutionResult:
    command: str
    returncode: int
    stdout: str
    stderr: str
    success: bool


def execute_command(command: str) -> CommandExecutionResult:
    """Execute a validated shell command and return structured output."""
    normalized = (command or "").strip()
    if not normalized:
        raise ValueError("Command cannot be empty.")

    try:
        completed = subprocess.run(
            normalized,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = (exc.stdout or "").strip()
        stderr = (exc.stderr or "").strip() or "Command timed out after 60 seconds."
        return CommandExecutionResult(
            command=normalized,
            returncode=124,
            stdout=stdout,
            stderr=stderr,
            success=False,
        )
    except FileNotFoundError:
        return CommandExecutionResult(
            command=normalized,
            returncode=127,
            stdout="",
            stderr="The shell command could not be executed because the command runtime is unavailable.",
            success=False,
        )

    return CommandExecutionResult(
        command=normalized,
        returncode=completed.returncode,
        stdout=(completed.stdout or "").strip(),
        stderr=(completed.stderr or "").strip(),
        success=completed.returncode == 0,
    )
