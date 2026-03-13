from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from guided.configure.schema import Configuration, Preference
from guided.preferences.command import app

runner = CliRunner()


def make_config(**kwargs) -> Configuration:
    return Configuration(**kwargs)


@pytest.fixture
def empty_config():
    return make_config()


@pytest.fixture
def config_with_preferences():
    return make_config(preferences={
        "theme": Preference(key="theme", value="dark"),
        "editor": Preference(key="editor", value="vim"),
    })


# list


def test_list_empty(empty_config):
    result = runner.invoke(app, ["list"], obj=empty_config)
    assert result.exit_code == 0
    assert "No preferences set" in result.output


def test_list_shows_preferences(config_with_preferences):
    result = runner.invoke(app, ["list"], obj=config_with_preferences)
    assert result.exit_code == 0
    assert "theme" in result.output
    assert "dark" in result.output
    assert "editor" in result.output
    assert "vim" in result.output


# get


def test_get_existing_preference(config_with_preferences):
    result = runner.invoke(app, ["get", "theme"], obj=config_with_preferences)
    assert result.exit_code == 0
    assert "dark" in result.output


def test_get_missing_preference(empty_config):
    result = runner.invoke(app, ["get", "theme"], obj=empty_config)
    assert result.exit_code == 1
    assert "not set" in result.output


# set


def test_set_new_preference(empty_config):
    saved = MagicMock()
    with patch("guided.preferences.command.save_config", saved):
        result = runner.invoke(app, ["set", "theme", "light"], obj=empty_config)
    assert result.exit_code == 0
    assert "set" in result.output
    saved.assert_called_once()
    config = saved.call_args[0][0]
    assert config.preferences["theme"].value == "light"


def test_set_overwrites_existing_preference(config_with_preferences):
    saved = MagicMock()
    with patch("guided.preferences.command.save_config", saved):
        result = runner.invoke(app, ["set", "theme", "light"], obj=config_with_preferences)
    assert result.exit_code == 0
    config = saved.call_args[0][0]
    assert config.preferences["theme"].value == "light"


# unset


def test_unset_existing_preference(config_with_preferences):
    saved = MagicMock()
    with patch("guided.preferences.command.save_config", saved):
        result = runner.invoke(app, ["unset", "theme"], obj=config_with_preferences)
    assert result.exit_code == 0
    assert "removed" in result.output
    saved.assert_called_once()
    config = saved.call_args[0][0]
    assert "theme" not in config.preferences


def test_unset_missing_preference(empty_config):
    with patch("guided.preferences.command.save_config") as saved:
        result = runner.invoke(app, ["unset", "theme"], obj=empty_config)
    assert result.exit_code == 1
    assert "not set" in result.output
    saved.assert_not_called()
