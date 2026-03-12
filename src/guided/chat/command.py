import sys
from pathlib import Path
from typing import Optional

import ollama
import rich
import typer
from rich.console import Console

from guided.chat.actions import ActionContext, default_registry
from guided.configure.config import get_default_config
from guided.skills.executor import execute_tool, skill_to_tool


class ChatSession:
    def __init__(self, config, messages: Optional[list] = None):
        self.config = config
        self.model: Optional[str] = None
        self.provider = None
        self.messages = messages if messages is not None else []
        self.registry = default_registry()
        self._console = Console()

        default_skills = get_default_config().skills
        all_skills = {**default_skills, **config.skills}
        self._skills_by_name = all_skills
        self._tools = [
            t
            for skill in all_skills.values()
            if (t := skill_to_tool(skill)) is not None
        ]

    def resolve_model(self, model: Optional[str] = None) -> str:
        """Resolve and set self.model from the config, returning the model name."""
        if model is None:
            model_cfg = next(
                (m for m in self.config.models.values() if m.is_default), None
            )
            if model_cfg is None:
                rich.print(
                    "[red]No model specified and no default model configured.[/red]"
                )
                rich.print(
                    "Run [bold]guide models set-default <name>[/bold] to set a default."
                )
                raise typer.Exit(1)
            self.model = model_cfg.name
            self._provider_key = model_cfg.provider
        elif model in self.config.models:
            model_cfg = self.config.models[model]
            self.model = model_cfg.name
            self._provider_key = model_cfg.provider
        else:
            # Treat as a bare model name; find an ollama provider to use
            self.model = model
            self._provider_key = next(
                (k for k, p in self.config.providers.items() if p.name == "ollama"),
                None,
            )
            if self._provider_key is None:
                rich.print(f"[red]No provider found for model '{model}'.[/red]")
                raise typer.Exit(1)

        return self.model

    def resolve_provider(self):
        """Resolve and set self.provider from the config, returning the provider."""
        provider_key = getattr(self, "_provider_key", None)
        if provider_key is None:
            raise RuntimeError("Call resolve_model() before resolve_provider()")

        self.provider = self.config.providers.get(provider_key)
        if self.provider is None:
            rich.print(f"[red]Provider '{provider_key}' not found in config.[/red]")
            raise typer.Exit(1)

        return self.provider

    def run(self):
        """Start the interactive chat loop."""
        if self.model is None or self.provider is None:
            raise RuntimeError(
                "Call resolve_model() and resolve_provider() before run()"
            )

        client = ollama.Client(host=self.provider.base_url)

        rich.print(
            f"[bold]Chatting with[/bold] [cyan]{self.model}[/cyan] via [cyan]{self.provider.name}[/cyan]"
        )
        rich.print("Type your message and press Enter. Press Ctrl+C to exit.")
        rich.print("Type [cyan]/help[/cyan] for available actions.\n")

        while True:
            try:
                self._console.out("\nYou:", style="dim", end="")
                user_input = typer.prompt("", prompt_suffix=" ")
            except (typer.Abort, KeyboardInterrupt, EOFError):
                rich.print("\n[dim]Goodbye.[/dim]")
                break

            if not user_input.strip():
                rich.print("[dim]Goodbye.[/dim]")
                break

            if user_input.strip().startswith("/"):
                action_context = ActionContext(
                    config=self.config, messages=self.messages, registry=self.registry
                )
                should_exit = self.registry.dispatch(user_input.strip(), action_context)
                if should_exit:
                    break
                continue

            self.messages.append({"role": "user", "content": user_input})
            self._send(client, disable_tools=False)

    def _execute_tool_calls(
        self, client, msg, disable_tools: bool = False
    ) -> Optional[object]:
        """If msg has tool calls, execute them and re-query until a plain response arrives.

        Returns the final message with no tool calls, or None if the initial msg had none.
        """
        if not msg.tool_calls:
            return None

        while msg.tool_calls:
            for tool_call in msg.tool_calls:
                fn = tool_call.function
                skill = self._skills_by_name.get(fn.name)
                if skill is None:
                    result = f"Error: unknown tool '{fn.name}'"
                else:
                    result = execute_tool(skill, dict(fn.arguments))
                self.messages.append({"role": "tool", "content": result})

            response = client.chat(
                model=self.model,
                messages=self.messages,
                tools=[] if disable_tools else (self._tools or None),
            )
            msg = response.message
            self.messages.append(msg)

        return msg

    def _send(self, client, disable_tools: bool = False):
        """Send the current message history, executing any tool calls, and print the reply."""
        try:
            with self._console.status("[bold magenta]Thinking...", spinner="dots"):
                response = client.chat(
                    model=self.model,
                    messages=self.messages,
                    tools=[] if disable_tools else (self._tools or None),
                )

            msg = response.message
            self.messages.append(msg)

            if not disable_tools and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    rich.print(
                        f"[dim]  → {tool_call.function.name}({dict(tool_call.function.arguments)})[/dim]"
                    )
                msg = self._execute_tool_calls(client, msg, disable_tools=disable_tools)

            self._console.out("\nAssistant: ", style="dim", end="")
            if msg.content:
                self._console.out(msg.content, end="")
            self._console.out("\n")

        except Exception as e:
            rich.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)

    def run_once(self, text: str, disable_tools: bool = False) -> None:
        """Send a single message from stdin and write the plain response to stdout."""
        self.messages.append({"role": "user", "content": text})
        client = ollama.Client(host=self.provider.base_url)
        try:
            response = client.chat(
                model=self.model,
                messages=self.messages,
                tools=[] if disable_tools else (self._tools or None),
            )
            msg = response.message
            self.messages.append(msg)

            if not disable_tools and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    fn = tool_call.function
                    skill = self._skills_by_name.get(fn.name)
                    result = (
                        execute_tool(skill, dict(fn.arguments))
                        if skill is not None
                        else f"Error: unknown tool '{fn.name}'"
                    )
                    self.messages.append({"role": "tool", "content": result})

                response = client.chat(
                    model=self.model,
                    messages=self.messages,
                    tools=[] if disable_tools else (self._tools or None),
                )
                msg = response.message
                self.messages.append(msg)

            if msg.content:
                sys.stdout.write(msg.content)

        except Exception as e:
            sys.stderr.write(f"Error: {e}")
            raise typer.Exit(1)


def chat(
    ctx: typer.Context,
    model: Optional[str] = typer.Argument(default=None, help="Model name to chat with"),
):
    """Chat interactively with a model, or pipe text via stdin for a single response."""
    is_interactive = sys.stdin.isatty()
    messages = []

    # Load and prefix AGENTS.md content
    agents_content = load_agents_md()
    if agents_content:
        if is_interactive:
            rich.print("[dim]Loaded agent context from AGENTS.md[/dim]")
        messages.append({"role": "system", "content": agents_content})

    session = ChatSession(config=ctx.obj, messages=messages)
    session.resolve_model(model)
    session.resolve_provider()

    if is_interactive:
        session.run()
    else:
        text = sys.stdin.read().strip()
        if text:
            session.run_once(text, disable_tools=True)


def load_agents_md() -> Optional[str]:
    """Load AGENTS.md from current directory or workspace, if it exists.

    Checks in order:
    1. Current directory's AGENTS.md
    2. .workspace/AGENTS.md (in workspace root)
    3. .workspace/context/AGENTS.md (in workspace context folder)
    """
    # Check current directory first
    current_agents = Path("AGENTS.md")
    if current_agents.exists():
        return current_agents.read_text().strip()

    # Check workspace locations
    workspace = Path(".workspace")
    if workspace.is_dir():
        # Check workspace root
        workspace_agents = workspace / "AGENTS.md"
        if workspace_agents.exists():
            return workspace_agents.read_text().strip()

        # Check workspace context folder
        context_agents = workspace / "context" / "AGENTS.md"
        if context_agents.exists():
            return context_agents.read_text().strip()

    return None
