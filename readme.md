# hello

`hello` is a Python CLI utility that turns natural-language prompts into safe shell commands with a guardrailed LangGraph workflow, secure API key storage, and local execution history.

## Features

- Natural-language to shell command conversion
- Secure LLM API key storage using the OS credential manager
- Safety validation against dangerous command patterns
- Human confirmation before executing a generated command
- Local SQLite history for recent commands
- Rich terminal output for commands and history

## Project structure

```text
hello/
├── pyproject.toml
├── readme.md
├── hello_cli/
│   ├── __init__.py
│   ├── __main__.py
│   ├── agent.py
│   ├── auth.py
│   ├── executor.py
│   ├── history.py
│   └── main.py
└── tests/
    └── test_history.py
```

## Setup

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

## Configure authentication

Set your LLM API key securely:

```bash
hello auth
```

This prompts for the API key without echoing it to the terminal and stores it in the OS keychain.

## Usage

Invoke the CLI with a plain-language request:

```bash
hello list the files in this directory
```

Or with a Git task:

```bash
hello commit the message "initial commit"
```

The system will:

1. Generate a command from your prompt.
2. Validate it against a blocklist of dangerous commands.
3. Show the command for confirmation.
4. Execute it if approved.
5. Record the result in local history.

## History

View recent commands:

```bash
hello history
```

This displays the most recent 10 interactions in a Rich table.

## Security model

The tool intentionally blocks patterns such as:

- `rm -rf`
- `mkfs`
- `dd if=` / `dd of=`
- `sudo rm`
- `poweroff`
- `reboot`
- destructive payload-style shell patterns

If a generated command matches a blocked pattern, it is refused before execution.

## Notes

- API keys are stored in the OS credential manager, not in a plaintext file.
- History is stored at `~/.hello_cli/history.db`.
- A command is only executed after explicit user confirmation.
