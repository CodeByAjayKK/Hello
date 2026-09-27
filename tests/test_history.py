from pathlib import Path

from typer.testing import CliRunner

from hello_cli.history import DB_PATH, ensure_database, fetch_recent_history, log_interaction
from hello_cli.main import app

runner = CliRunner()


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


def test_cli_accepts_freeform_prompt_as_default_command(monkeypatch):
    monkeypatch.setattr("hello_cli.main.get_api_key", lambda: "test-key")
    monkeypatch.setattr("hello_cli.main.run_agent", lambda prompt: {"generated_command": "ls -la", "is_safe": True, "execution_result": "success"})
    monkeypatch.setattr("hello_cli.main.execute_command", lambda command: type("Result", (), {"success": True, "returncode": 0, "stdout": "ok", "stderr": ""})())
    monkeypatch.setattr("hello_cli.main.log_interaction", lambda *args, **kwargs: None)

    result = runner.invoke(app, ['list the files in this directory'])

    assert result.exit_code == 0
    assert "Command succeeded" in result.stdout


def test_help_auth_history_commands_do_not_trigger_api_verification(monkeypatch):
    monkeypatch.setattr("hello_cli.main.get_api_key", lambda: (_ for _ in ()).throw(AssertionError("API key validation should not run for built-ins")))

    help_result = runner.invoke(app, ["help"])
    auth_result = runner.invoke(app, ["auth"])
    history_result = runner.invoke(app, ["history"])

    assert help_result.exit_code == 0
    assert auth_result.exit_code == 0
    assert history_result.exit_code == 0


def test_get_api_key_uses_saved_provider_when_no_provider_passed(monkeypatch):
    def fake_keyring_get_password(service, name):
        if name == "llm_provider":
            return "groq"
        if name == "groq_api_key":
            return "groq-key"
        return None

    monkeypatch.setattr("hello_cli.auth.keyring.get_password", fake_keyring_get_password)
    monkeypatch.setattr("hello_cli.auth.os.getenv", lambda name: None)

    from hello_cli.auth import get_api_key

    assert get_api_key() == "groq-key"
