"""SQLite-backed command history for the hello CLI."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.table import Table

DB_DIR = Path.home() / ".hello_cli"
DB_PATH = DB_DIR / "history.db"


def ensure_database() -> None:
    """Create the local SQLite database and schema if it does not already exist."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_prompt TEXT NOT NULL,
            generated_command TEXT NOT NULL,
            success_status INTEGER NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def log_interaction(user_prompt: str, generated_command: str, success_status: bool) -> None:
    """Save a single CLI interaction to the local history database."""
    ensure_database()
    timestamp = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO history (timestamp, user_prompt, generated_command, success_status) VALUES (?, ?, ?, ?)",
        (timestamp, user_prompt, generated_command, int(bool(success_status))),
    )
    conn.commit()
    conn.close()


def fetch_recent_history(limit: int = 10) -> list[dict[str, str | int]]:
    """Fetch the most recent N entries from local history."""
    ensure_database()
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT timestamp, user_prompt, generated_command, success_status FROM history ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()

    records: list[dict[str, str | int]] = []
    for timestamp, user_prompt, generated_command, success_status in rows:
        records.append(
            {
                "timestamp": timestamp,
                "user_prompt": user_prompt,
                "generated_command": generated_command,
                "success_status": bool(success_status),
            }
        )
    return list(reversed(records))


def show_history(limit: int = 10) -> None:
    """Display the most recent command history in a Rich table."""
    console = Console()
    rows = fetch_recent_history(limit=limit)
    table = Table(title=f"Recent commands (last {min(len(rows), limit)})")
    table.add_column("Time", style="cyan")
    table.add_column("Prompt", style="magenta")
    table.add_column("Command", style="green")
    table.add_column("Status", style="bold")

    if not rows:
        console.print("No command history yet.")
        return

    for row in rows:
        status = "OK" if row["success_status"] else "FAIL"
        status_style = "green" if row["success_status"] else "red"
        table.add_row(
            str(row["timestamp"])[:19],
            str(row["user_prompt"]),
            str(row["generated_command"]),
            f"[{status_style}]{status}[/{status_style}]",
        )

    console.print(table)
