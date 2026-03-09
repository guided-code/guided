from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from guided.configure.schema import Configuration, Provider
from guided.providers.command import app

runner = CliRunner()


def make_config(**kwargs) -> Configuration:
    return Configuration(**kwargs)


@pytest.fixture
def empty_config():
    return make_config()


@pytest.fixture
def config_with_provider():
    return make_config(
        providers={"ollama": Provider(name="ollama", base_url="http://localhost:11434")}
    )


# list


def test_list_empty(empty_config):
    result = runner.invoke(app, ["list"], obj=empty_config)
    assert result.exit_code == 0
    assert "No providers configured" in result.output


def test_list_shows_providers(config_with_provider):
    result = runner.invoke(app, ["list"], obj=config_with_provider)
    assert result.exit_code == 0
    assert "ollama" in result.output
    assert "http://localhost:11434" in result.output


# add


def test_add_provider(empty_config):
    saved = MagicMock()
    with patch("guided.providers.command.save_config", saved):
        result = runner.invoke(app, ["add", "openai", "https://api.openai.com/v1"], obj=empty_config)
    assert result.exit_code == 0
    assert "added" in result.output
    saved.assert_called_once()
    config = saved.call_args[0][0]
    assert "openai" in config.providers
    assert config.providers["openai"].base_url == "https://api.openai.com/v1"


def test_add_duplicate_provider(config_with_provider):
    with patch("guided.providers.command.save_config") as saved:
        result = runner.invoke(app, ["add", "ollama", "http://localhost:11434"], obj=config_with_provider)
    assert result.exit_code == 1
    assert "already exists" in result.output
    saved.assert_not_called()


# remove


def test_remove_provider(config_with_provider):
    saved = MagicMock()
    with patch("guided.providers.command.save_config", saved):
        result = runner.invoke(app, ["remove", "ollama"], obj=config_with_provider)
    assert result.exit_code == 0
    assert "removed" in result.output
    saved.assert_called_once()
    config = saved.call_args[0][0]
    assert "ollama" not in config.providers


def test_remove_nonexistent_provider(empty_config):
    with patch("guided.providers.command.save_config") as saved:
        result = runner.invoke(app, ["remove", "nonexistent"], obj=empty_config)
    assert result.exit_code == 1
    assert "not found" in result.output
    saved.assert_not_called()
