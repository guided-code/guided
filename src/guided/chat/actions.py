from __future__ import annotations

from abc import ABC, abstractmethod

from typing import Any

import rich
from pydantic import BaseModel, ConfigDict

from guided.configure.config import load_agents_md
from guided.configure.schema import Configuration, Preference


class ActionContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    config: Configuration
    messages: list
    registry: ActionRegistry
    session: Any = None


class Action(ABC):
    """Base class for all actions."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Action name (without leading slash)."""
        ...

    @property
    def aliases(self) -> list[str]:
        """Additional names that can be used to invoke this action."""
        return []

    @property
    def description(self) -> str:
        return ""

    @abstractmethod
    def execute(self, ctx: ActionContext, args: str = "") -> bool:
        """Execute the action. Returns True to exit the chat loop."""
        ...


class ExitAction(Action):
    """Exits interactive chat mode."""

    @property
    def name(self) -> str:
        return "exit"

    @property
    def description(self) -> str:
        return "Exit the chat session"

    @property
    def aliases(self) -> list[str]:
        return ["quit", "bye", "q"]

    def execute(self, ctx: ActionContext, args: str = "") -> bool:
        rich.print("[dim]Goodbye.[/dim]")
        return True


class HelpAction(Action):
    """Shows available actions."""

    @property
    def name(self) -> str:
        return "help"

    @property
    def description(self) -> str:
        return "List available actions"

    @property
    def aliases(self) -> list[str]:
        return ["h", "?"]

    def execute(self, ctx: ActionContext, args: str = "") -> bool:
        rich.print("")
        rich.print("Use `!` to run commands on the containerized workspace.")
        rich.print("")
        rich.print("[bold]Available actions:[/bold]")
        for name in ctx.registry.get_all_action_names():
            action = ctx.registry.actions[name]
            rich.print(f"  [cyan]/{name}[/cyan] — {action.description}")
        rich.print()
        return False


class ClearAction(Action):
    """Clears the current chat messages context."""

    @property
    def name(self) -> str:
        return "clear"

    @property
    def description(self) -> str:
        return "Clear the current chat messages"

    def execute(self, ctx: ActionContext, args: str = "") -> bool:
        ctx.messages.clear()
        agents_content = load_agents_md()
        if agents_content:
            ctx.messages.append({"role": "system", "content": agents_content})
        rich.print("[green]Chat messages cleared.[/green]")
        if ctx.session is not None:
            ctx.session.reset_session_id()
        return False


class HistoryAction(Action):
    """Shows all previous chat messages."""

    @property
    def name(self) -> str:
        return "history"

    @property
    def description(self) -> str:
        return "Show all previous chat messages"

    def execute(self, ctx: ActionContext, args: str = "") -> bool:
        if not ctx.messages:
            rich.print("[dim]No messages in the chat history.[/dim]")
            return False

        rich.print("\n[bold]Chat History:[/bold]")
        for i, msg in enumerate(ctx.messages, start=1):
            role = msg.get("role", "unknown")

            rich.print(f"\n[bold]--- Message {i} ({role.capitalize()}) ---[/bold]")
            if "error" in msg:
                stacktrace = msg.get("stacktrace", "")
                rich.print(f"[red]{stacktrace}[/red]")
                error = msg.get("error", "")
                rich.print(f"[red]{error}[/red]")
            else:
                content = msg.get("content", "")
                rich.print(f"[cyan]{content}[/cyan]")
            rich.print("[dim]---[/dim]")

        rich.print("")
        return False


class SetPreferenceAction(Action):
    """Sets a preference for the current chat session."""

    @property
    def name(self) -> str:
        return "set"

    @property
    def description(self) -> str:
        return "Set a preference for this session: /set <key> <value>"

    def execute(self, ctx: ActionContext, args: str = "") -> bool:
        parts = args.split(maxsplit=1)
        if len(parts) != 2:
            rich.print("[red]Usage: /set <key> <value>[/red]")
            return False
        key, value = parts
        ctx.config.preferences[key] = Preference(key=key, value=value)
        rich.print(
            f"[green]Preference '{key}' set to '{value}' for this session.[/green]"
        )
        return False


class GetPreferenceAction(Action):
    """Gets a preference value for the current chat session."""

    @property
    def name(self) -> str:
        return "get"

    @property
    def description(self) -> str:
        return "Get a preference value: /get <key>"

    def execute(self, ctx: ActionContext, args: str = "") -> bool:
        key = args.strip()
        if not key:
            rich.print("[red]Usage: /get <key>[/red]")
            return False
        if key not in ctx.config.preferences:
            rich.print(f"[red]Preference '{key}' not set.[/red]")
            return False
        rich.print(ctx.config.preferences[key].value)
        return False


class UnsetPreferenceAction(Action):
    """Unsets a preference for the current chat session."""

    @property
    def name(self) -> str:
        return "unset"

    @property
    def description(self) -> str:
        return "Unset a preference for this session: /unset <key>"

    def execute(self, ctx: ActionContext, args: str = "") -> bool:
        key = args.strip()
        if not key:
            rich.print("[red]Usage: /unset <key>[/red]")
            return False
        if key not in ctx.config.preferences:
            rich.print(f"[red]Preference '{key}' not set.[/red]")
            return False
        del ctx.config.preferences[key]
        rich.print(f"[green]Preference '{key}' unset for this session.[/green]")
        return False


class InitAction(Action):
    """Initializes a workspace in the current directory."""

    @property
    def name(self) -> str:
        return "init"

    @property
    def description(self) -> str:
        return "Initialize a workspace in the current directory"

    def execute(self, ctx: ActionContext, args: str = "") -> bool:
        from guided.workspace.command import initialize_workspace

        initialize_workspace()
        return False


class CompactAction(Action):
    """Compacts the chat history into a summary to save context window space."""

    @property
    def name(self) -> str:
        return "compact"

    @property
    def description(self) -> str:
        return "Compact chat history by summarizing previous messages"

    def execute(self, ctx: ActionContext, args: str = "") -> bool:
        if len(ctx.messages) <= 2:
            rich.print("[dim]Not enough messages to compact.[/dim]")
            return False

        rich.print("[dim]Compacting messages...[/dim]")

        system_msgs = [m for m in ctx.messages if m.get("role") == "system"]
        chat_msgs = [m for m in ctx.messages if m.get("role") != "system"]

        if not chat_msgs:
            rich.print("[dim]No chat messages to compact.[/dim]")
            return False

        prompt = ""
        for msg in chat_msgs:
            role = msg.get("role", "unknown").capitalize()
            # Try to get the main content, or error if it was a failure
            content = msg.get("content") or msg.get("error") or ""
            if content:
                prompt += f"{role}: {content}\n\n"

        try:
            import torch
            from llmlingua import PromptCompressor
        except ImportError:
            rich.print(
                "[red]The llmlingua library is required for message compaction. "
                "Please install the cuda optional dependencies.[/red]"
            )
            return False

        if not torch.cuda.is_available():
            rich.print(
                "[red]CUDA is required to use the llmlingua-2 model for message compaction.[/red]"
            )
            return False

        try:
            status = None
            if hasattr(ctx.session, "_console"):
                status = ctx.session._console.status(
                    "[bold magenta]Compacting...", spinner="dots"
                )
                status.start()

            llm_lingua = PromptCompressor(
                model_name="microsoft/llmlingua-2-xlm-roberta-large-meetingbank",
                use_llmlingua2=True,  # Whether to use llmlingua-2
            )
            compressed = llm_lingua.compress_prompt(prompt, rate=0.33)

            if status is not None:
                status.stop()

            summary = compressed["compressed_prompt"]

            ctx.messages.clear()
            ctx.messages.extend(system_msgs)
            ctx.messages.append(
                {
                    "role": "system",
                    "content": f"Previous conversation summary:\n{summary}",
                }
            )

            rich.print("[green]Chat history successfully compacted.[/green]")
            if ctx.session is not None:
                ctx.session.reset_session_id()
        except Exception as e:
            if "status" in locals() and status is not None:
                status.stop()
            rich.print(f"[red]Error compacting messages: {e}[/red]")

        return False


class ActionRegistry:
    """Registry for actions."""

    def __init__(self) -> None:
        self.actions: dict[str, Action] = {}
        self.main_names: set[str] = set()

    def register(self, action: Action) -> None:
        if action.name in self.actions:
            raise ValueError(f"Action '{action.name}' is already registered")
        self.actions[action.name] = action
        self.main_names.add(action.name)
        for alias in action.aliases:
            if alias in self.actions:
                raise ValueError(
                    f"Alias '{alias}' for action '{action.name}' conflicts with existing action"
                )
            self.actions[alias] = action

    def dispatch(self, user_input: str, ctx: ActionContext) -> bool | None:
        """Dispatch a slash action. Returns True to exit, False to continue,
        or None if the input is not an action."""
        if not user_input.startswith("/"):
            return None

        parts = user_input[1:].split(maxsplit=1)
        name = parts[0]
        args = parts[1] if len(parts) > 1 else ""

        action = self.actions.get(name)
        if action is None:
            rich.print(f"[red]Unknown action: /{name}[/red]")
            return False

        return action.execute(ctx, args)

    def get_all_action_names(self) -> list[str]:
        """Return a list of all action names (excluding aliases)."""
        return sorted(self.main_names)


def get_actions_registry() -> ActionRegistry:
    registry = ActionRegistry()

    default_actions = [
        InitAction(),
        ClearAction(),
        CompactAction(),
        ExitAction(),
        GetPreferenceAction(),
        HistoryAction(),
        SetPreferenceAction(),
        UnsetPreferenceAction(),
        HelpAction(),
    ]
    for action in default_actions:
        registry.register(action)

    return registry
