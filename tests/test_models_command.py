from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from guided.configure.schema import GuidedConfig, Model, Provider
from guided.models.command import app

runner = CliRunner()


def make_config(**kwargs) -> GuidedConfig:
    return GuidedConfig(**kwargs)


@pytest.fixture
def empty_config():
    return make_config()


@pytest.fixture
def config_with_model():
    return make_config(
        providers={"ollama": Provider(name="ollama", base_url="http://localhost:11434")},
        models={"llama3": Model(name="llama3", provider="ollama")},
    )


# list


def test_list_empty_no_ollama(empty_config):
    with (
        patch("guided.models.command.load_config", return_value=empty_config),
        patch("guided.models.command.ollama.Client") as mock_client_cls,
    ):
        mock_client_cls.return_value.list.side_effect = Exception("unreachable")
        result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "No models configured" in result.output


def test_list_shows_configured_models(config_with_model):
    with (
        patch("guided.models.command.load_config", return_value=config_with_model),
        patch("guided.models.command.ollama.Client") as mock_client_cls,
    ):
        mock_client_cls.return_value.list.return_value = MagicMock(models=[])
        result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "llama3" in result.output
    assert "ollama" in result.output


def test_list_shows_ollama_discovered_models():
    config = make_config(
        providers={"ollama": Provider(name="ollama", base_url="http://localhost:11434")}
    )
    discovered = MagicMock()
    discovered.model = "mistral"
    with (
        patch("guided.models.command.load_config", return_value=config),
        patch("guided.models.command.ollama.Client") as mock_client_cls,
    ):
        mock_client_cls.return_value.list.return_value = MagicMock(models=[discovered])
        result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "mistral" in result.output


def test_list_ollama_unreachable_shows_warning():
    config = make_config(
        providers={"ollama": Provider(name="ollama", base_url="http://localhost:11434")}
    )
    with (
        patch("guided.models.command.load_config", return_value=config),
        patch("guided.models.command.ollama.Client") as mock_client_cls,
    ):
        mock_client_cls.return_value.list.side_effect = Exception("connection refused")
        result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "Warning" in result.output


# add


def test_add_model(empty_config):
    saved = MagicMock()
    with (
        patch("guided.models.command.load_config", return_value=empty_config),
        patch("guided.models.command.save_config", saved),
    ):
        result = runner.invoke(app, ["add", "llama3", "ollama"])
    assert result.exit_code == 0
    assert "added" in result.output
    saved.assert_called_once()
    config = saved.call_args[0][0]
    assert "llama3" in config.models
    assert config.models["llama3"].provider == "ollama"


def test_add_duplicate_model(config_with_model):
    with (
        patch("guided.models.command.load_config", return_value=config_with_model),
        patch("guided.models.command.save_config") as saved,
    ):
        result = runner.invoke(app, ["add", "llama3", "ollama"])
    assert result.exit_code == 1
    assert "already exists" in result.output
    saved.assert_not_called()


# remove


def test_remove_model(config_with_model):
    saved = MagicMock()
    with (
        patch("guided.models.command.load_config", return_value=config_with_model),
        patch("guided.models.command.save_config", saved),
    ):
        result = runner.invoke(app, ["remove", "llama3"])
    assert result.exit_code == 0
    assert "removed" in result.output
    saved.assert_called_once()
    config = saved.call_args[0][0]
    assert "llama3" not in config.models


def test_remove_nonexistent_model(empty_config):
    with (
        patch("guided.models.command.load_config", return_value=empty_config),
        patch("guided.models.command.save_config") as saved,
    ):
        result = runner.invoke(app, ["remove", "nonexistent"])
    assert result.exit_code == 1
    assert "not found" in result.output
    saved.assert_not_called()
