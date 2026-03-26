import pytest
from unittest.mock import patch

from guided.chat.actions import (
    Action,
    ActionContext,
    ActionRegistry,
    ExitAction,
    GetPreferenceAction,
    HelpAction,
    InitAction,
    SetPreferenceAction,
    UnsetPreferenceAction,
    get_actions_registry,
)
from guided.configure.schema import Configuration, Preference


@pytest.fixture(autouse=True)
def auto_confirm():
    """Auto-confirm all prompt_toolkit confirm dialogs in tests."""
    with patch("guided.workspace.command.confirm", return_value=True):
        yield


def make_ctx(registry=None, config=None) -> ActionContext:
    return ActionContext(
        config=config if config is not None else Configuration(),
        messages=[],
        registry=registry or get_actions_registry(),
    )





def test_exit_action_returns_true(capsys):
    ctx = make_ctx()
    result = ExitAction().execute(ctx)
    assert result is True
    assert "Goodbye" in capsys.readouterr().out





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





def test_set_preference_returns_false(capsys):
    config = Configuration()
    ctx = make_ctx(config=config)
    result = SetPreferenceAction().execute(ctx, "theme dark")
    assert result is False


def test_set_preference_stores_preference():
    config = Configuration()
    ctx = make_ctx(config=config)
    SetPreferenceAction().execute(ctx, "theme dark")
    assert config.preferences["theme"] == Preference(key="theme", value="dark")


def test_set_preference_overwrites_existing():
    config = Configuration(
        preferences={"theme": Preference(key="theme", value="light")}
    )
    ctx = make_ctx(config=config)
    SetPreferenceAction().execute(ctx, "theme dark")
    assert config.preferences["theme"].value == "dark"


def test_set_preference_missing_args_prints_usage(capsys):
    config = Configuration()
    ctx = make_ctx(config=config)
    result = SetPreferenceAction().execute(ctx, "theme")
    assert result is False
    assert "Usage" in capsys.readouterr().out
    assert "theme" not in config.preferences


def test_set_preference_no_args_prints_usage(capsys):
    config = Configuration()
    ctx = make_ctx(config=config)
    result = SetPreferenceAction().execute(ctx, "")
    assert result is False
    assert "Usage" in capsys.readouterr().out


def test_set_preference_value_with_spaces():
    config = Configuration()
    ctx = make_ctx(config=config)
    SetPreferenceAction().execute(ctx, "prompt you are a helpful assistant")
    assert config.preferences["prompt"].value == "you are a helpful assistant"


def test_set_preference_does_not_persist(capsys):
    """Session-scoped: save_config should never be called."""
    from unittest.mock import patch

    config = Configuration()
    ctx = make_ctx(config=config)
    with patch("guided.configure.config.save_config") as mock_save:
        SetPreferenceAction().execute(ctx, "theme dark")
    mock_save.assert_not_called()





def test_get_preference_returns_value(capsys):
    config = Configuration(preferences={"theme": Preference(key="theme", value="dark")})
    ctx = make_ctx(config=config)
    result = GetPreferenceAction().execute(ctx, "theme")
    assert result is False
    assert "dark" in capsys.readouterr().out


def test_get_preference_missing_key_prints_error(capsys):
    config = Configuration()
    ctx = make_ctx(config=config)
    result = GetPreferenceAction().execute(ctx, "theme")
    assert result is False
    assert "not set" in capsys.readouterr().out


def test_get_preference_no_args_prints_usage(capsys):
    config = Configuration()
    ctx = make_ctx(config=config)
    result = GetPreferenceAction().execute(ctx, "")
    assert result is False
    assert "Usage" in capsys.readouterr().out





def test_unset_preference_removes_key():
    config = Configuration(preferences={"theme": Preference(key="theme", value="dark")})
    ctx = make_ctx(config=config)
    result = UnsetPreferenceAction().execute(ctx, "theme")
    assert result is False
    assert "theme" not in config.preferences


def test_unset_preference_missing_key_prints_error(capsys):
    config = Configuration()
    ctx = make_ctx(config=config)
    result = UnsetPreferenceAction().execute(ctx, "theme")
    assert result is False
    assert "not set" in capsys.readouterr().out


def test_unset_preference_no_args_prints_usage(capsys):
    config = Configuration()
    ctx = make_ctx(config=config)
    result = UnsetPreferenceAction().execute(ctx, "")
    assert result is False
    assert "Usage" in capsys.readouterr().out





def test_init_action_returns_false(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ctx = make_ctx()
    result = InitAction().execute(ctx)
    assert result is False
    assert "Workspace initialized" in capsys.readouterr().out


def test_init_action_describes_initialization(capsys, tmp_path, monkeypatch):
    """Test that init action creates workspace with correct structure."""
    monkeypatch.chdir(tmp_path)
    ctx = make_ctx()
    result = InitAction().execute(ctx)
    assert result is False
    output = capsys.readouterr().out

    assert "Workspace initialized" in output
    assert "name:" in output
    assert "folders:" in output

    workspace = tmp_path / ".workspace"
    assert workspace.exists()
    assert (workspace / "config.yaml").exists()
    assert (workspace / "decisions").exists()
    assert (workspace / "transcripts").exists()
    assert (workspace / "context").exists()





# InitAction integration test


def test_init_action_creates_workspace(capsys, tmp_path, monkeypatch):
    """Test that init action creates workspace with correct structure."""
    monkeypatch.chdir(tmp_path)
    ctx = make_ctx()
    result = InitAction().execute(ctx)
    assert result is False
    output = capsys.readouterr().out

    assert "Workspace initialized" in output
    assert "name:" in output
    assert "folders:" in output

    workspace = tmp_path / ".workspace"
    assert workspace.exists()
    assert (workspace / "config.yaml").exists()
    assert (workspace / "decisions").exists()
    assert (workspace / "transcripts").exists()
    assert (workspace / "context").exists()


# ActionRegistry.dispatch


def test_dispatch_exit():
    registry = get_actions_registry()
    ctx = make_ctx(registry)
    assert registry.dispatch("/exit", ctx) is True


def test_dispatch_init(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    registry = get_actions_registry()
    ctx = make_ctx(registry)
    assert registry.dispatch("/init", ctx) is False


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





def test_get_all_action_names_returns_init():
    registry = get_actions_registry()
    names = registry.get_all_action_names()
    assert "init" in names

    # test_get_all_action_names_returns_main_names_only():
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
