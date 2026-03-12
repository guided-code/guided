import logging
import sys
from pathlib import Path
from typing import Optional, Self

import ollama
import rich
import typer
from rich.console import Console

from guided import get_version
from guided.chat.actions import ActionContext, get_actions_registry
from guided.configure.schema import Skill
from guided.environment import is_debug
from guided.skills.container import read_file
from guided.skills.executor import execute_skill
from guided.skills.web_search import search_web_text

DEFAULT_TOOLS = [read_file, search_web_text]

logger = logging.getLogger("guided.core")


class ChatSession:
    def __init__(
        self,
        config,
        messages: Optional[list] = None,
        is_logging: bool = False,
        is_interactive: bool = False,
    ):
        self.config = config
        self.model: Optional[str] = None
        self.provider = None
        self.messages = messages if messages is not None else []
        self.is_logging = is_logging
        self.is_interactive = is_interactive
        self.registry = get_actions_registry()
        self._console = Console()
        self._tools = []
        self._skills_by_name = {}

    def resolve_model(self, model: Optional[str] = None) -> Self:
        """Set model or fallback to default model configuration"""

        # Use default model
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

        # Use specified model
        elif model in self.config.models:
            model_cfg = self.config.models[model]
            self.model = model_cfg.name
            self._provider_key = model_cfg.provider

        if self.model is None:
            if self.is_logging:
                rich.print("[red]Unable to set model or not found in config.[/red]")
            raise typer.Exit(1)

        return self

    def resolve_provider(self) -> Self:
        """Setup configured provider from model"""
        provider_key = getattr(self, "_provider_key", None)
        if provider_key is None:
            raise RuntimeError("Call resolve_model() before resolve_provider()")

        self.provider = self.config.providers.get(provider_key)
        if self.provider is None:
            if self.is_logging:
                rich.print(f"[red]Provider '{provider_key}' not found in config.[/red]")
            raise typer.Exit(1)

        return self

    def resolve_default_skills(self) -> Self:
        """Setup default tools and skills"""

        # Maps existing default tools to skills
        self._tools = DEFAULT_TOOLS
        for tool in self._tools:
            skill = Skill(
                name=tool.__name__,
                description=tool.__doc__,
                parameters={},
                handler=tool,
            )

            self._skills_by_name[skill.name] = skill

        return self

    def run(self, text: Optional[str] = None, disable_tools: bool = False):
        """Start the interactive chat loop or process a single message."""
        if self.model is None or self.provider is None:
            raise RuntimeError(
                "Call resolve_model() and resolve_provider() before run()"
            )

        client = ollama.Client(host=self.provider.base_url)

        # Send once
        if not self.is_interactive:
            self.messages.append({"role": "user", "content": text})
            self._send(client, disable_tools=disable_tools)

        # Interactive loop
        else:
            rich.print("[bold][Guided][/bold]")
            rich.print("Version: ", get_version())
            rich.print("")
            rich.print(
                f"[bold]Chatting with[/bold] [cyan]{self.model}[/cyan] via [cyan]{self.provider.name}[/cyan]"
            )
            rich.print("Type your message and press Enter. Press Ctrl+C to exit.")
            rich.print("Type [cyan]/help[/cyan] for available actions.\n")

            while True:
                # User input prompt
                try:
                    self._console.out("\n[You]:", style="dim", end="")
                    user_input = typer.prompt("", prompt_suffix=" ")
                except (typer.Abort, KeyboardInterrupt, EOFError):
                    rich.print("\n[dim]Goodbye.[/dim]")
                    break

                # Exit
                if not user_input.strip():
                    rich.print("[dim]Goodbye.[/dim]")
                    break

                # Action
                if user_input.strip().startswith("/"):
                    action_context = ActionContext(
                        config=self.config,
                        messages=self.messages,
                        registry=self.registry,
                    )
                    should_exit = self.registry.dispatch(
                        user_input.strip(), action_context
                    )
                    if should_exit:
                        break
                    continue

                # Process response
                self.messages.append({"role": "user", "content": user_input})
                self._send(client, disable_tools=disable_tools)

    def _execute_tool_calls(
        self, client, msg, disable_tools: bool = False
    ) -> Optional[object]:
        """If msg has tool calls, execute them and re-query until a plain response arrives.

        Returns the final message with no tool calls, or None if the initial msg had none.
        """
        if not msg.tool_calls:
            return None

        while msg.tool_calls:
            if self.is_logging:
                for tool_call in msg.tool_calls:
                    rich.print(
                        f"[dim]  → {tool_call.function.name}({dict(tool_call.function.arguments)})[/dim]"
                    )

            for tool_call in msg.tool_calls:
                fn = tool_call.function
                skill = self._skills_by_name.get(fn.name)
                if skill is None:
                    result = f"Error: unknown tool '{fn.name}'"
                else:
                    exec = execute_skill(skill, **dict(fn.arguments))
                    result = exec.result
                self.messages.append({"role": "tool", "content": result})

            if self.is_logging:
                with self._console.status("[bold magenta]Thinking...", spinner="dots"):
                    response = client.chat(
                        model=self.model,
                        messages=self.messages,
                        tools=[] if disable_tools else (self._tools or None),
                    )
            else:
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
            if self.is_logging:
                with self._console.status("[bold magenta]Thinking...", spinner="dots"):
                    response = client.chat(
                        model=self.model,
                        messages=self.messages,
                        tools=[] if disable_tools else (self._tools or None),
                    )
            else:
                response = client.chat(
                    model=self.model,
                    messages=self.messages,
                    tools=[] if disable_tools else (self._tools or None),
                )

            msg = response.message
            self.messages.append(msg)

            # Tool call
            if not disable_tools and msg.tool_calls:
                msg = self._execute_tool_calls(client, msg, disable_tools=disable_tools)

            # Allow completion
            if msg is None:
                return

            # Response
            if self.is_logging:
                self._console.out("\n[Assistant]: ", style="dim", end="")
                if msg.content:
                    self._console.out(msg.content, end="")
                self._console.out("\n")
            else:
                if msg.content:
                    sys.stdout.write(msg.content)

        except Exception as e:
            # Print stacktrace
            logging.error("Exception occurred", exc_info=True)

            if self.is_logging:
                rich.print(f"[red]Error: {e}[/red]")
            else:
                sys.stderr.write(f"Error: {e}\n")
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

    session = (
        ChatSession(
            config=ctx.obj,
            messages=messages,
            is_logging=is_interactive or is_debug(),
            is_interactive=is_interactive,
        )
        .resolve_model(model)
        .resolve_provider()
        .resolve_default_skills()
    )

    if is_interactive:
        session.run()
    else:
        text = sys.stdin.read().strip()
        if text:
            session.run(text=text)


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
