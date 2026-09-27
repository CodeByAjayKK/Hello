from __future__ import annotations

from typing import Literal, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from .auth import get_api_key, get_provider


class State(TypedDict):
    user_prompt: str
    generated_command: str
    is_safe: bool
    execution_result: str


DANGEROUS_PATTERNS: tuple[str, ...] = (
    "rm -rf",
    "mkfs",
    "dd if=",
    "dd of=",
    "/dev/sda",
    "chmod 777 /",
    "curl | sh",
    "wget | sh",
    "sudo rm",
    "poweroff",
    "reboot",
    ":(){:|:&};:",
)


def _build_model():
    """Create the configured chat model from the provider-specific API key."""
    provider = get_provider()
    api_key = get_api_key(provider)
    import os

    os.environ["HELLO_LLM_PROVIDER"] = provider

    if provider == "openai":
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as exc:  # pragma: no cover - dependency issue at runtime
            raise RuntimeError(
                "langchain-openai is required. Install the project dependencies with pip install -e ."
            ) from exc
        os.environ["OPENAI_API_KEY"] = api_key
        return ChatOpenAI(model="gpt-4o-mini", temperature=0)

    if provider == "anthropic":
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError as exc:  # pragma: no cover - dependency issue at runtime
            raise RuntimeError(
                "langchain-anthropic is required. Install the project dependencies for Anthropic support."
            ) from exc
        os.environ["ANTHROPIC_API_KEY"] = api_key
        return ChatAnthropic(model="claude-3-5-haiku-latest", temperature=0)

    if provider == "google":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError as exc:  # pragma: no cover - dependency issue at runtime
            raise RuntimeError(
                "langchain-google-genai is required. Install the project dependencies for Google Gemini support."
            ) from exc
        os.environ["GOOGLE_API_KEY"] = api_key
        return ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)

    if provider == "groq":
        try:
            from langchain_groq import ChatGroq
        except ImportError as exc:  # pragma: no cover - dependency issue at runtime
            raise RuntimeError(
                "langchain-groq is required. Install the project dependencies for Groq support."
            ) from exc
        os.environ["GROQ_API_KEY"] = api_key
        model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        return ChatGroq(model=model_name, temperature=0, api_key=api_key)

    raise RuntimeError(f"Unsupported provider selected: {provider}")


def _generate_command_node(state: State) -> State:
    model = _build_model()
    system_prompt = (
        "You are a command generator for a shell environment. "
        "Return only a single raw shell command with no markdown fences, no explanations, and no surrounding text. "
        "Do not include commentary or extra formatting. "
        "The command must be safe, concise, and executable."
    )

    response = model.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=state["user_prompt"]),
        ]
    )

    command = (response.content or "").strip()
    command = command.replace("```", "").strip()
    if not command:
        raise ValueError("The model returned an empty command.")

    state["generated_command"] = command
    state["execution_result"] = ""
    return state


def _validate_command_node(state: State) -> State:
    command = (state.get("generated_command") or "").strip().lower()
    is_safe = True
    for pattern in DANGEROUS_PATTERNS:
        if pattern.lower() in command:
            is_safe = False
            break

    state["is_safe"] = is_safe
    if not is_safe:
        state["execution_result"] = "Blocked by security policy: dangerous command pattern detected."
    return state


def _route_after_validation(state: State) -> Literal["hitl", END]:
    return "hitl" if state.get("is_safe") else END


def _hitl_node(state: State) -> State:
    if not state.get("is_safe"):
        return state

    console = Console()
    command = state["generated_command"]
    console.print(
        Panel.fit(
            f"[bold yellow]Review the following command before execution:[/bold yellow]\n\n[cyan]{command}[/cyan]",
            border_style="yellow",
        )
    )

    confirmed = Confirm.ask("Run this command? [y/N]")
    if not confirmed:
        state["execution_result"] = "Command execution cancelled by user."
        return state

    state["execution_result"] = "Approved by user."
    return state


def _build_graph() -> StateGraph:
    workflow = StateGraph(State)
    workflow.add_node("generator", _generate_command_node)
    workflow.add_node("validator", _validate_command_node)
    workflow.add_node("hitl", _hitl_node)

    workflow.set_entry_point("generator")
    workflow.add_edge("generator", "validator")
    workflow.add_conditional_edges("validator", _route_after_validation, {"hitl": "hitl", END: END})
    workflow.add_edge("hitl", END)
    return workflow


def run_agent(user_prompt: str) -> State:
    """Run the safety-guarded LangGraph pipeline for a user request."""
    state: State = {
        "user_prompt": user_prompt,
        "generated_command": "",
        "is_safe": False,
        "execution_result": "",
    }

    compiled = _build_graph().compile()
    return compiled.invoke(state)
