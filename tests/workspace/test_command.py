import pytest
import yaml
from unittest.mock import patch
from typer.testing import CliRunner

from guided.workspace.command import SUBDIRS, WORKSPACE_DIR, app, workspace_key

runner = CliRunner()


@pytest.fixture(autouse=True)
def auto_confirm():
    """Auto-confirm all prompt_toolkit confirm dialogs in tests."""
    with patch("guided.workspace.command.confirm", return_value=True):
        yield


def _init_workspace(tmp_path, *extra_args):
    """Helper: invoke init and assert it succeeded."""
    result = runner.invoke(app, ["init", str(tmp_path), *extra_args])
    assert result.exit_code == 0, result.output
    return result


# init


def test_init_creates_workspace(tmp_path):
    result = _init_workspace(tmp_path)
    workspace = tmp_path / WORKSPACE_DIR
    assert workspace.is_dir()
    assert (workspace / "config.yaml").is_file()
    for subdir in SUBDIRS:
        assert (workspace / subdir).is_dir()


def test_init_uses_directory_name_as_default_name(tmp_path):
    result = _init_workspace(tmp_path)
    assert tmp_path.name in result.output


def test_init_custom_name(tmp_path):
    result = _init_workspace(tmp_path, "--name", "my-project")
    assert "my-project" in result.output


def test_init_default_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert (tmp_path / WORKSPACE_DIR).is_dir()


def test_init_fails_if_already_exists(tmp_path):
    _init_workspace(tmp_path)
    result = runner.invoke(app, ["init", str(tmp_path)])
    assert result.exit_code == 0
    assert "Workspace exists" in result.output


def test_init_fails_if_path_not_found(tmp_path):
    missing = tmp_path / "does_not_exist"
    result = runner.invoke(app, ["init", str(missing)])
    assert result.exit_code == 1
    assert "does not exist" in result.output


# info


def test_info_shows_workspace_details(tmp_path):
    _init_workspace(tmp_path, "--name", "test-ws")
    result = runner.invoke(app, ["info", str(tmp_path)])
    assert result.exit_code == 0
    assert "test-ws" in result.output
    for subdir in SUBDIRS:
        assert subdir in result.output


def test_info_fails_if_no_workspace(tmp_path):
    result = runner.invoke(app, ["info", str(tmp_path)])
    assert result.exit_code == 1
    assert "No workspace found" in result.output


def test_info_default_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0
    assert tmp_path.name in result.output


# init — upgrade / key mismatch scenarios


def test_init_notifies_on_upgrade_when_workspace_key_is_none(tmp_path):
    """When workspace_key is absent (created by an older CLI), init notifies and sets the key."""
    _init_workspace(tmp_path)
    # Simulate an old workspace by clearing workspace_key from config
    config_path = tmp_path / WORKSPACE_DIR / "config.yaml"
    with open(config_path) as f:
        data = yaml.safe_load(f)
    data["workspace_key"] = None
    with open(config_path, "w") as f:
        yaml.dump(data, f)

    result = runner.invoke(app, ["init", str(tmp_path)])
    assert result.exit_code == 0
    assert "upgraded" in result.output.lower()

    # Key should now be written to config
    with open(config_path) as f:
        updated = yaml.safe_load(f)
    assert updated["workspace_key"] == workspace_key()


def test_init_fails_if_workspace_key_mismatch(tmp_path):
    """When workspace_key exists but doesn't match the current machine, init exits with an error."""
    _init_workspace(tmp_path)
    config_path = tmp_path / WORKSPACE_DIR / "config.yaml"
    with open(config_path) as f:
        data = yaml.safe_load(f)
    data["workspace_key"] = "different_machine_key"
    with open(config_path, "w") as f:
        yaml.dump(data, f)

    result = runner.invoke(app, ["init", str(tmp_path)])
    assert result.exit_code == 1
    assert "workspace update" in result.output
