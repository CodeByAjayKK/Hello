# hiwiz

`hiwiz` is a Python CLI that turns natural-language requests into safe shell commands using a guardrailed LLM workflow, secure API key storage, and local execution history.

## Features

- Natural-language shell command generation
- Secure storage of LLM API keys in the OS keychain
- Dangerous command blocking before execution
- Human confirmation for generated commands
- Local SQLite history of recent interactions
- Rich terminal output for help, auth, and history

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

## Authentication

Set your LLM API key securely:

```bash
hiwiz auth
```

You can choose a provider with:

```bash
hiwiz auth --provider groq
```

This prompts for the API key without echoing it to the terminal and stores it in the OS keychain.

You can also configure the provider and API key through environment variables:

```bash
export HELLO_LLM_PROVIDER=groq
export GROQ_API_KEY="your-api-key"
```

You do not need to set these variables if you already configured a provider via `hiwiz auth` or if you want to use the default provider (`openai`).

Model selection is also optional. If you do not set a model variable, hiwiz uses a built-in default for that provider:

```bash
export OPENAI_MODEL="gpt-4o-mini"
export ANTHROPIC_MODEL="claude-3-5-haiku-latest"
export GOOGLE_MODEL="gemini-1.5-flash"
export GROQ_MODEL="llama-3.3-70b-versatile"
```

Supported providers are: `openai`, `anthropic`, `google`, and `groq`.

## Usage

Use built-in commands:

```bash
hiwiz help
hiwiz history
```

Send a natural-language request as a prompt:

```bash
hiwiz "list the files in this directory"
hiwiz "show git status"
hiwiz "commit the message 'initial commit'"
```

The tool will:

1. Generate a shell command from the prompt.
2. Validate it against a blocklist of dangerous patterns.
3. Show the command for confirmation.
4. Execute it if approved.
5. Record the result in local history.

## History

View recent command history:

```bash
hiwiz history
```

## Security model

The tool intentionally blocks common destructive patterns such as:

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
- History is stored locally in the app data/history database for the project.
- A command is only executed after explicit user confirmation.
- The public usage pattern is: `hiwiz "your prompt"` for normal requests and `hiwiz help` / `hiwiz auth` / `hiwiz history` for built-ins.
