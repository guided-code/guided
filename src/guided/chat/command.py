import logging
import sys
import textwrap
import traceback
from datetime import datetime
from typing import List, Optional, Self

import ollama
import rich
import uuid

import typer
import yaml
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
from guided.skills.executor import execute_skill
from guided.skills import DEFAULT_TOOLS
from guided.skills.container import exec_command
from guided.workspace.command import initialize_workspace, find_workspace_root

logger = logging.getLogger("guided.core")


class ChatSession:
    def __init__(
        self,
        config,
        messages: Optional[list] = None,
        use_thinking: bool = True,
        use_tools: bool = True,
    ):
        self.config = config
        self.model: Optional[str] = None
        self.provider = None
        self.messages = [] if messages is None else messages
        self.use_thinking = use_thinking
        self.use_tools = use_tools
        self.registry = get_actions_registry()
        self._console = Console()
        self._tools = []
        self._skills_by_name = {}
        self._prompt_sesion = None
        self._prompt_history = None
        self._transcript_file = None
        self.session_id = uuid.uuid4().hex[:8]

    def reset_session_id(self):
        self.session_id = uuid.uuid4().hex[:8]
        if getattr(self, "_transcript_file", None) is not None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            self._transcript_file = (
                self._transcript_file.parent / f"{self.session_id}_{timestamp}.yaml"
            )

    def _save_transcript(self):
        if getattr(self, "_transcript_file", None) is not None:
            with open(self._transcript_file, "w") as f:
                yaml.dump(self.messages, f, default_flow_style=False, sort_keys=False)

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
            HTML("\n\n<seagreen>[You]: </seagreen>"),
            lexer=PygmentsLexer(HtmlLexer),
            style=style,
            include_default_pygments_style=False,
        )

    def run_once(self, text: Optional[str] = None):
        """Start processing a single message"""
        workspace_root = find_workspace_root(".")
        initialize_workspace(workspace_root)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self._transcript_file = (
            workspace_root
            / ".workspace"
            / "transcripts"
            / f"{self.session_id}_{timestamp}.yaml"
        )

        self.messages.append({"role": "user", "content": text})
        self._save_transcript()

        # Run-time loop
        client = ollama.Client(host=self.provider.base_url)

        # Process response
        self.in_thinking = False
        self._send(client)

    def run(self):
        """Start the interactive chat loop"""
        self.in_thinking = False

        if self.model is None or self.provider is None:
            raise RuntimeError(
                "Call resolve_model() and resolve_provider() before run()"
            )

        # Prompt user
        rich.print("[bold][Guided][/bold]")
        rich.print("Version: ", get_version())
        rich.print(
            f"[bold]Chatting with[/bold] [cyan]{self.model}[/cyan] via [cyan]{self.provider.name}[/cyan]"
        )
        rich.print("")
        rich.print("Type your message and press Enter. Press Ctrl+C to exit.")
        rich.print("Type [cyan]/help[/cyan] for available actions.\n")

        # Initialize workspace by default
        workspace_root = find_workspace_root(".")
        initialize_workspace(workspace_root)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self._transcript_file = (
            workspace_root
            / ".workspace"
            / "transcripts"
            / f"{self.session_id}_{timestamp}.yaml"
        )

        client = ollama.Client(host=self.provider.base_url)

        # Interactive loop
        while True:
            # User input prompt
            try:
                user_input = self.prompt_user()

            except (typer.Abort, KeyboardInterrupt, EOFError):
                rich.print("\n[dim]Goodbye.[/dim]")
                break

            # Action
            if user_input.strip().startswith("/"):
                action_context = ActionContext(
                    config=self.config,
                    messages=self.messages,
                    registry=self.registry,
                    session=self,
                )
                should_exit = self.registry.dispatch(user_input.strip(), action_context)
                if should_exit:
                    break
                continue

            # Container exec
            if user_input.strip().startswith("!"):
                cmd_to_run = user_input.strip()[1:].strip()
                if cmd_to_run:
                    try:
                        status = None
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
                        logging.error(
                            "Exception occurred during command execution", exc_info=True
                        )
                continue

            # Process response
            self.messages.append({"role": "user", "content": user_input})
            self._save_transcript()
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
            self._save_transcript()
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
                rich.print(
                    f"\n[dim]  → {handler.name}({dict(handler.arguments)})[/dim]",
                    end="",
                )
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
            self._save_transcript()

    def _send(self, client):
        """Send the current message history, executing any tool calls, and print the reply.

        Returns:
            List of tool calls if the message contains tool calls, empty list otherwise.
        """
        disabled_tools = not self.use_tools
        tool_calls = []
        try:
            status = None
            status = self._console.status("[bold magenta]Processing...", spinner="dots")
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
                    tool_calls.extend(message.tool_calls)

                # Started thinking
                if message.thinking and not self.in_thinking:
                    self.in_thinking = True
                    self._console.out(
                        "\n\n[Assistant (Thinking)]: ", style="dim magenta", end=""
                    )

                # Not thinking
                if not message.thinking:
                    # Stopped thinking
                    if self.in_thinking:
                        if message.content != "":
                            self._console.out(
                                "\n\n[Assistant]: ", style="dim magenta", end=""
                            )
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
            self._save_transcript()

        except ollama.ResponseError as e:
            rich.print(f"\n[red]Error: {e}[/red]")

            stacktrace = traceback.format_exc()
            self.messages.append(
                {"role": "assistant", "error": str(e), "stacktrace": stacktrace}
            )
            self._save_transcript()
            return tool_calls

        except Exception as e:
            # Print stacktrace
            logging.error("Exception occurred", exc_info=True)
            rich.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)

        return tool_calls


def get_system_prompt() -> str:
    agents_content = load_agents_md()
    system_prompt = ""
    if agents_content:
        system_prompt += textwrap.dedent("""
            Use the AGENT.md file to guide your responses.
                
            ```@AGENTS.md
            """)
        system_prompt += agents_content
        system_prompt += "\n```\n\n"
    system_prompt += textwrap.dedent("""
        Additional instructions:
            * Commands are executed within a container with the current working directory mounted as `/workspace`. 
            * Ignore the `.workspace/` folder and its contents unless explicitly asked.
            * Services are deployed using Kubernetes and can be interacted with using tools
            * Write a Dockerfile to build image(s) as necessary and a set of manifest files `manifests/` to deploy
        """)
    return system_prompt


def run_chat(
    config: Configuration,
    model: Optional[str] = None,
    use_thinking: bool = True,
    use_tools: bool = True,
):
    is_interactive = sys.stdin.isatty()
    messages = [
        {
            "role": "system",
            "content": get_system_prompt(),
        }
    ]
    session = (
        ChatSession(
            config=config,
            messages=messages,
            use_thinking=use_thinking,
            use_tools=is_interactive and use_tools,
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
            session.run_once(text=text)
