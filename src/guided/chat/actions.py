from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import rich

if TYPE_CHECKING:
    from guided.configure.schema import Configuration


@dataclass
class ActionContext:
    config: "Configuration"
    messages: list
    registry: "ActionRegistry"


class Action(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Action name (without leading slash)."""
        ...

    @property
    def description(self) -> str:
        return ""

    @abstractmethod
    def execute(self, ctx: ActionContext, args: str = "") -> bool:
        """Execute the action. Returns True to exit the chat loop."""
        ...


class ExitAction(Action):
    @property
    def name(self) -> str:
        return "exit"

    @property
    def description(self) -> str:
        return "Exit the chat session"

    def execute(self, ctx: ActionContext, args: str = "") -> bool:
        rich.print("[dim]Goodbye.[/dim]")
        return True


class HelpAction(Action):
    @property
    def name(self) -> str:
        return "help"

    @property
    def description(self) -> str:
        return "List available actions"

    def execute(self, ctx: ActionContext, args: str = "") -> bool:
        rich.print("\n[bold]Available actions:[/bold]")
        for action in ctx.registry.actions.values():
            rich.print(f"  [cyan]/{action.name}[/cyan] — {action.description}")
        rich.print()
        return False


class ActionRegistry:
    def __init__(self) -> None:
        self.actions: dict[str, Action] = {}

    def register(self, action: Action) -> None:
        self.actions[action.name] = action

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


def default_registry() -> ActionRegistry:
    registry = ActionRegistry()
    registry.register(ExitAction())
    registry.register(HelpAction())
    return registry
