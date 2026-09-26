from pathlib import Path

from hello_cli.history import DB_PATH, ensure_database, fetch_recent_history, log_interaction


def test_history_database_and_logging(tmp_path, monkeypatch):
    monkeypatch.setattr("hello_cli.history.DB_PATH", tmp_path / "history.db")
    monkeypatch.setattr("hello_cli.history.DB_DIR", tmp_path)

    ensure_database()
    log_interaction("list files", "ls -la", True)
    log_interaction("show git status", "git status", False)

    records = fetch_recent_history(limit=10)

    assert len(records) == 2
    assert records[0]["user_prompt"] == "show git status"
    assert records[0]["generated_command"] == "git status"
    assert records[0]["success_status"] is False
    assert (tmp_path / "history.db").exists()
