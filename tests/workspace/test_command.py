import pytest
from typer.testing import CliRunner

from guided.workspace.command import SUBDIRS, WORKSPACE_DIR, app

runner = CliRunner()


# init


def test_init_creates_workspace(tmp_path):
    result = runner.invoke(app, ["init", str(tmp_path)])
    assert result.exit_code == 0
    workspace = tmp_path / WORKSPACE_DIR
    assert workspace.is_dir()
    assert (workspace / "config.yaml").is_file()
    for subdir in SUBDIRS:
        assert (workspace / subdir).is_dir()


def test_init_uses_directory_name_as_default_name(tmp_path):
    result = runner.invoke(app, ["init", str(tmp_path)])
    assert result.exit_code == 0
    assert tmp_path.name in result.output


def test_init_custom_name(tmp_path):
    result = runner.invoke(app, ["init", str(tmp_path), "--name", "my-project"])
    assert result.exit_code == 0
    assert "my-project" in result.output


def test_init_default_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert (tmp_path / WORKSPACE_DIR).is_dir()


def test_init_fails_if_already_exists(tmp_path):
    runner.invoke(app, ["init", str(tmp_path)])
    result = runner.invoke(app, ["init", str(tmp_path)])
    assert result.exit_code == 1
    assert "already exists" in result.output


def test_init_fails_if_path_not_found(tmp_path):
    missing = tmp_path / "does_not_exist"
    result = runner.invoke(app, ["init", str(missing)])
    assert result.exit_code == 1
    assert "does not exist" in result.output


# info


def test_info_shows_workspace_details(tmp_path):
    runner.invoke(app, ["init", str(tmp_path), "--name", "test-ws"])
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
