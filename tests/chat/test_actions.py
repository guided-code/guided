from unittest.mock import MagicMock

import pytest

from guided.chat.actions import (
    Action,
    ActionContext,
    ActionRegistry,
    ExitAction,
    HelpAction,
    get_actions_registry,
)


def make_ctx(registry=None) -> ActionContext:
    return ActionContext(
        config=MagicMock(),
        messages=[],
        registry=registry or get_actions_registry(),
    )


# ExitAction


def test_exit_action_name():
    assert ExitAction().name == "exit"


def test_exit_action_returns_true(capsys):
    ctx = make_ctx()
    result = ExitAction().execute(ctx)
    assert result is True
    assert "Goodbye" in capsys.readouterr().out


# HelpAction


def test_help_action_name():
    assert HelpAction().name == "help"


def test_help_action_returns_false(capsys):
    ctx = make_ctx()
    result = HelpAction().execute(ctx)
    assert result is False


def test_help_action_lists_actions(capsys):
    ctx = make_ctx()
    HelpAction().execute(ctx)
    output = capsys.readouterr().out
    assert "/exit" in output
    assert "/help" in output


# ActionRegistry.dispatch


def test_dispatch_exit():
    registry = get_actions_registry()
    ctx = make_ctx(registry)
    assert registry.dispatch("/exit", ctx) is True


def test_dispatch_help():
    registry = get_actions_registry()
    ctx = make_ctx(registry)
    assert registry.dispatch("/help", ctx) is False


def test_dispatch_unknown(capsys):
    registry = get_actions_registry()
    ctx = make_ctx(registry)
    result = registry.dispatch("/nope", ctx)
    assert result is False
    assert "Unknown action" in capsys.readouterr().out


def test_dispatch_non_action_returns_none():
    registry = get_actions_registry()
    ctx = make_ctx(registry)
    assert registry.dispatch("hello", ctx) is None


def test_dispatch_passes_args():
    registry = ActionRegistry()
    received = {}

    class EchoAction(Action):
        @property
        def name(self):
            return "echo"

        def execute(self, ctx, args=""):
            received["args"] = args
            return False

    registry.register(EchoAction())
    ctx = make_ctx(registry)
    registry.dispatch("/echo foo bar", ctx)
    assert received["args"] == "foo bar"


# get_actions_registry


def test_actions_registry_has_exit_and_help():
    registry = get_actions_registry()
    assert "exit" in registry.actions
    assert "help" in registry.actions


# Alias dispatch


def test_dispatch_quit_alias():
    registry = get_actions_registry()
    ctx = make_ctx(registry)
    assert registry.dispatch("/quit", ctx) is True


def test_dispatch_bye_alias():
    registry = get_actions_registry()
    ctx = make_ctx(registry)
    assert registry.dispatch("/bye", ctx) is True


def test_dispatch_q_alias():
    registry = get_actions_registry()
    ctx = make_ctx(registry)
    assert registry.dispatch("/q", ctx) is True


def test_dispatch_h_alias():
    registry = get_actions_registry()
    ctx = make_ctx(registry)
    assert registry.dispatch("/h", ctx) is False


def test_dispatch_question_mark_alias():
    registry = get_actions_registry()
    ctx = make_ctx(registry)
    assert registry.dispatch("/?", ctx) is False


# get_all_action_names


def test_get_all_action_names_returns_main_names_only():
    registry = get_actions_registry()
    names = registry.get_all_action_names()
    assert "exit" in names
    assert "help" in names
    # aliases should not appear in main names
    assert "quit" not in names
    assert "bye" not in names
    assert "q" not in names
    assert "h" not in names


def test_get_all_action_names_is_sorted():
    registry = get_actions_registry()
    names = registry.get_all_action_names()
    assert names == sorted(names)


# ActionRegistry registration


def test_register_duplicate_name_raises():
    registry = ActionRegistry()

    class Foo(Action):
        @property
        def name(self):
            return "foo"

        def execute(self, ctx, args=""):
            return False

    registry.register(Foo())
    with pytest.raises(ValueError, match="already registered"):
        registry.register(Foo())


def test_register_conflicting_alias_raises():
    registry = ActionRegistry()

    class FooAction(Action):
        @property
        def name(self):
            return "foo"

        @property
        def aliases(self):
            return ["shared"]

        def execute(self, ctx, args=""):
            return False

    class BarAction(Action):
        @property
        def name(self):
            return "bar"

        @property
        def aliases(self):
            return ["shared"]

        def execute(self, ctx, args=""):
            return False

    registry.register(FooAction())
    with pytest.raises(ValueError, match="conflicts"):
        registry.register(BarAction())
