import logging
import sys
import traceback
from typing import List, Optional, Self

import ollama
import rich
import typer
from prompt_toolkit import HTML, PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.shortcuts import confirm
from prompt_toolkit.styles.pygments import style_from_pygments_cls
from pygments.lexers.html import HtmlLexer
from pygments.styles import get_style_by_name
from rich.console import Console

from guided import get_version
from guided.chat.actions import ActionContext, get_actions_registry
from guided.configure.config import load_agents_md
from guided.configure.schema import Configuration, Skill
from guided.environment import is_debug
from guided.skills.executor import execute_skill
from guided.skills import DEFAULT_TOOLS
from guided.skills.container import exec_command

logger = logging.getLogger("guided.core")


class ChatSession:
    def __init__(
        self,
        config,
        messages: Optional[list] = None,
        is_logging: bool = False,
        is_interactive: bool = False,
        use_thinking: bool = True,
        use_tools: bool = True,
    ):
        self.config = config
        self.model: Optional[str] = None
        self.provider = None
        self.messages = messages if messages is not None else []
        self.is_logging = is_logging
        self.is_interactive = is_interactive
        self.use_thinking = use_thinking
        self.use_tools = use_tools
        self.registry = get_actions_registry()
        self._console = Console()
        self._tools = []
        self._skills_by_name = {}
        self._prompt_sesion = None
        self._prompt_history = None

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
        self._tools = DEFAULT_TOOLS.copy()
        for tool in self._tools:
            skill = Skill(
                name=tool.__name__,
                description=tool.__doc__,
                parameters={},
                handler=tool,
            )

            self._skills_by_name[skill.name] = skill

        return self

    def get_prompt_session(self) -> PromptSession:
        """Get the prompt session for the chat"""
        if self._prompt_sesion is None:
            self._prompt_history = InMemoryHistory()
            self._prompt_sesion = PromptSession(history=self._prompt_history)
        return self._prompt_sesion

    def prompt_user(self) -> str:
        style = style_from_pygments_cls(get_style_by_name("monokai"))
        return self.get_prompt_session().prompt(
            HTML("\n<seagreen>[You]: </seagreen>"),
            lexer=PygmentsLexer(HtmlLexer),
            style=style,
            include_default_pygments_style=False,
        )

    def run(self, text: Optional[str] = None):
        """Start the interactive chat loop or process a single message."""
        self.in_thinking = False

        if self.model is None or self.provider is None:
            raise RuntimeError(
                "Call resolve_model() and resolve_provider() before run()"
            )

        client = ollama.Client(host=self.provider.base_url)

        # Send once
        if not self.is_interactive:
            self.messages.append({"role": "user", "content": text})
            while tool_calls := self._send(client):
                self._execute_tool_calls(client, tool_calls)

        # Interactive loop
        else:
            rich.print("[bold][Guided][/bold]")
            rich.print("Version: ", get_version())
            rich.print(
                f"[bold]Chatting with[/bold] [cyan]{self.model}[/cyan] via [cyan]{self.provider.name}[/cyan]"
            )
            rich.print("")
            rich.print("Type your message and press Enter. Press Ctrl+C to exit.")
            rich.print("Type [cyan]/help[/cyan] for available actions.\n")

            while True:
                # User input prompt
                try:
                    user_input = self.prompt_user()

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

                # Container exec
                if user_input.strip().startswith("!"):
                    cmd_to_run = user_input.strip()[1:].strip()
                    if cmd_to_run:
                        try:
                            status = None
                            if self.is_logging:
                                status = self._console.status(
                                    f"[bold magenta]Executing `{cmd_to_run}`...[/bold magenta]",
                                    spinner="dots",
                                )
                                status.start()

                            output = exec_command(cmd_to_run)

                            if status is not None:
                                status.stop()

                            rich.print(output)
                        except Exception as e:
                            if "status" in locals() and status is not None:
                                status.stop()
                            rich.print(f"[red]Error executing command: {e}[/red]")
                    continue

                # Process response
                self.messages.append({"role": "user", "content": user_input})
                while tool_calls := self._send(client):
                    self._execute_tool_calls(client, tool_calls)

    def _execute_tool_calls(self, client, tool_calls: List) -> Optional[object]:
        """If msg has tool calls, execute them and re-query until a plain response arrives."""
        empty_tool_calls = not tool_calls
        disabled_tools = not self.use_tools

        if empty_tool_calls:
            return
        elif disabled_tools:
            self.messages.append({"role": "tool", "content": "Tools are disabled."})
            return

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
                if not self.is_interactive:
                    result = f"Tool ['{handler.name}'] use not confirmed in non-interactive mode."
                else:
                    rich.print("")
                    if confirm(
                        message=f"Confirm tool [{handler.name}] use? ",
                        suffix="(y/[n]) ",
                    ):
                        exec = execute_skill(skill, **dict(handler.arguments))
                        result = exec.result
                    else:
                        result = f"Tool ['{handler.name}'] use cancelled by user."

            # Append results
            self.messages.append(
                {"role": "tool", "tool_call_id": handler.name, "content": result}
            )

    def _send(self, client):
        """Send the current message history, executing any tool calls, and print the reply.

        Returns:
            List of tool calls if the message contains tool calls, empty list otherwise.
        """
        disabled_tools = not self.use_tools
        tool_calls = []
        try:
            status = None
            if self.is_logging:
                status = self._console.status(
                    "[bold magenta]Processing...", spinner="dots"
                )
                status.start()

            # Send messages to model
            stream = client.chat(
                model=self.model,
                messages=self.messages,
                tools=[] if disabled_tools else (self._tools or None),
                stream=True,
                think=True,
            )

            if status is not None:
                status.stop()

            # Stream response
            thinking = ""
            content = ""
            for chunk in stream:
                message = chunk.message

                # Tool call
                if not disabled_tools and message.tool_calls:
                    if self.is_logging:
                        for tool_call in message.tool_calls:
                            rich.print(
                                f"\n[dim]  → {tool_call.function.name}({dict(tool_call.function.arguments)})[/dim]",
                                end="",
                            )
                    tool_calls.extend(message.tool_calls)

                # Started thinking
                if message.thinking and not self.in_thinking:
                    self.in_thinking = True
                    if self.is_logging:
                        self._console.out(
                            "\n\n[Assistant (Thinking)]: ", style="dim magenta", end=""
                        )
                    else:
                        self._console.out("<think>")

                # Not thinking
                if not message.thinking:
                    # Stopped thinking
                    if self.in_thinking:
                        if message.content != "":
                            if self.is_logging:
                                self._console.out(
                                    "\n\n[Assistant]: ", style="dim magenta", end=""
                                )
                            else:
                                self._console.out("</think>")
                    self.in_thinking = False

                # Echo thinking
                if self.in_thinking:
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

        except ollama.ResponseError as e:
            if self.is_logging:
                rich.print(f"[red]Error: {e}[/red]")
            else:
                sys.stderr.write(f"Error: {e}\n")

            stacktrace = traceback.format_exc()
            self.messages.append(
                {"role": "assistant", "error": str(e), "stacktrace": stacktrace}
            )
            return tool_calls

        except Exception as e:
            # Print stacktrace
            logging.error("Exception occurred", exc_info=True)

            if self.is_logging:
                rich.print(f"[red]Error: {e}[/red]")
            else:
                sys.stderr.write(f"Error: {e}\n")
            raise typer.Exit(1)

        return tool_calls


def run_chat(
    config: Configuration,
    model: Optional[str] = None,
    use_thinking: bool = True,
    use_tools: bool = True,
):
    is_interactive = sys.stdin.isatty()
    messages = []

    # Load and prefix AGENTS.md content
    agents_content = load_agents_md()
    if agents_content:
        if is_interactive:
            rich.print("[dim]Loaded agent context from AGENTS.md[/dim]")
        messages.append(
            {"role": "system", "content": f"```@AGENTS.md\n{agents_content}```"}
        )

    session = (
        ChatSession(
            config=config,
            messages=messages,
            is_logging=is_interactive or is_debug(),
            is_interactive=is_interactive,
            use_thinking=use_thinking,
            use_tools=use_tools,
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
