import logging
import sys
from typing import Optional, Self, List

import ollama
import rich
import typer
from rich.console import Console

from guided import get_version
from guided.chat.actions import ActionContext, get_actions_registry
from guided.configure.schema import Configuration, Skill
from guided.environment import is_debug
from guided.skills.container import read_file
from guided.skills.executor import execute_skill
from guided.skills.web_search import search_web_text
from guided.configure.config import load_agents_md

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
            while tool_calls := self._send(client, disable_tools=disable_tools):
                self._execute_tool_calls(
                    client, tool_calls, disable_tools=disable_tools
                )

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
                while tool_calls := self._send(client, disable_tools=disable_tools):
                    self._execute_tool_calls(
                        client, tool_calls, disable_tools=disable_tools
                    )

    def _execute_tool_calls(
        self, client, tool_calls: List, disable_tools: bool = False
    ) -> Optional[object]:
        """If msg has tool calls, execute them and re-query until a plain response arrives."""
        if not tool_calls:
            return

        # Display tool calls
        if self.is_logging:
            for tool_call in tool_calls:
                rich.print(
                    f"[dim]  → {tool_call.function.name}({dict(tool_call.function.arguments)})[/dim]"
                )

        # Call all tools
        for tool_call in tool_calls:
            # Requested tool
            handler = tool_call.function

            # Find tool call
            skill = self._skills_by_name.get(handler.name)

            # Unrecognized tool
            if skill is None:
                result = f"Error: unknown skill '{handler.name}'"

            # Execute tool
            else:
                exec = execute_skill(skill, **dict(handler.arguments))
                result = exec.result

            # Append results
            self.messages.append({"role": "tool", "content": result})

    def _send(self, client, disable_tools: bool = False):
        """Send the current message history, executing any tool calls, and print the reply.

        Returns:
            List of tool calls if the message contains tool calls, empty list otherwise.
        """
        try:
            status = None
            if self.is_logging:
                status = self._console.status(
                    "[bold magenta]Processing...", spinner="dots"
                )
                status.start()

            stream = client.chat(
                model=self.model,
                messages=self.messages,
                tools=[] if disable_tools else (self._tools or None),
                stream=True,
                think=True,
            )

            if status is not None:
                status.stop()

            # Stream response
            in_thinking = False
            thinking = ""
            content = ""
            for chunk in stream:
                message = chunk.message

                # Tool call
                if not disable_tools and message.tool_calls:
                    if self.is_logging:
                        self._console.out("")
                    return message.tool_calls

                # Started thinking
                if message.thinking and not in_thinking:
                    in_thinking = True
                    if self.is_logging:
                        self._console.out(
                            "\n[Assistant (Thinking)]: ", style="dim magenta", end=""
                        )
                    else:
                        self._console.out("<think>")

                # Not thinking
                if not message.thinking:
                    # Stopped thinking
                    if in_thinking:
                        if self.is_logging:
                            self._console.out(
                                "\n\n[Assistant]: ", style="dim magenta", end=""
                            )
                        else:
                            self._console.out("\n</think>")
                    in_thinking = False

                # Echo thinking
                if in_thinking:
                    thinking += message.thinking
                    self._console.out(message.thinking, style="dim", end="")

                # Echo content
                else:
                    content += message.content
                    self._console.out(message.content, end="")

            # Collect complete thoughts and message
            self.messages.append(
                {"role": "assistant", "thinking": thinking, "content": content}
            )
            if self.is_logging:
                self._console.out("")

        except Exception as e:
            # Print stacktrace
            logging.error("Exception occurred", exc_info=True)

            if self.is_logging:
                rich.print(f"[red]Error: {e}[/red]")
            else:
                sys.stderr.write(f"Error: {e}\n")
            raise typer.Exit(1)

        return []


def run_chat(
    config: Configuration,
    model: Optional[str] = None,
):
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
            config=config,
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
