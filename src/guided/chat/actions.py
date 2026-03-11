from abc import ABC, abstractmethod
from dataclasses import dataclass
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
    @property
    def name(self) -> str:
        return "help"

    @property
    def description(self) -> str:
        return "List available actions"

    def execute(self, ctx: ActionContext, args: str = "") -> bool:
        rich.print("\n[bold]Available actions:[/bold]")
        for name in ctx.registry.get_all_action_names():
            action = ctx.registry.actions[name]
            rich.print(f"  [cyan]/{name}[/cyan] — {action.description}")
        rich.print()
        return False


class ActionRegistry:
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


def default_registry() -> ActionRegistry:
    registry = ActionRegistry()
    registry.register(ExitAction())
    registry.register(HelpAction())
    return registry
