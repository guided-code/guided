from unittest.mock import MagicMock, patch

import pytest
import typer
from typer.testing import CliRunner

from guided.chat.command import chat
from guided.configure.schema import Configuration, Model, Provider

runner = CliRunner()
app = typer.Typer()
app.command()(chat)


def make_config(**kwargs) -> Configuration:
    return Configuration(**kwargs)


OLLAMA_PROVIDER = Provider(name="ollama", base_url="http://localhost:11434")


@pytest.fixture
def config_with_model():
    return make_config(
        providers={"ollama": OLLAMA_PROVIDER},
        models={"codellama": Model(name="codellama:34b-python", provider="ollama")},
    )


@pytest.fixture
def config_with_default():
    return make_config(
        providers={"ollama": OLLAMA_PROVIDER},
        models={"llama3": Model(name="llama3", provider="ollama", is_default=True)},
    )


@pytest.fixture
def empty_config():
    return make_config()


def _mock_response(content: str) -> MagicMock:
    response = MagicMock()
    response.message.content = content
    response.message.tool_calls = None
    return response


# No model specified, no default configured


def test_chat_no_model_no_default(empty_config):
    result = runner.invoke(app, [], obj=empty_config)
    assert result.exit_code == 1
    assert "No model specified" in result.output


# No model specified, default configured via is_default=True attribute


def test_chat_uses_default_model(config_with_default):
    with patch("guided.chat.command.ollama.Client") as mock_client_cls:
        mock_client_cls.return_value.chat.return_value = _mock_response("Hello!")
        result = runner.invoke(app, [], obj=config_with_default, input="hi\n\n")
    assert result.exit_code == 0
    assert "Hello!" in result.output
    mock_client_cls.return_value.chat.assert_called_once()


# Model with default=False is not used as default


def test_chat_no_default_when_default_false(config_with_model):
    result = runner.invoke(app, [], obj=config_with_model)
    assert result.exit_code == 1
    assert "No model specified" in result.output


# Model specified by config key


def test_chat_model_by_config_key(config_with_model):
    with patch("guided.chat.command.ollama.Client") as mock_client_cls:
        mock_client_cls.return_value.chat.return_value = _mock_response("Hi there!")
        result = runner.invoke(
            app, ["llama3"], obj=config_with_model, input="hello\n\n"
        )
    assert result.exit_code == 0
    assert "Hi there!" in result.output
    mock_client_cls.return_value.chat.assert_called_once()


# Model specified as bare name (not in config)


def test_chat_bare_model_name():
    config = make_config(providers={"ollama": OLLAMA_PROVIDER}, models={})
    with patch("guided.chat.command.ollama.Client") as mock_client_cls:
        mock_client_cls.return_value.chat.return_value = _mock_response("Sure!")
        result = runner.invoke(app, ["codellama"], obj=config, input="hey\n\n")
    assert result.exit_code == 0
    call_args = mock_client_cls.return_value.chat.call_args
    assert call_args.kwargs["model"] == "codellama"


# Provider not found


def test_chat_provider_not_found():
    config = make_config(
        providers={},
        models={"mymodel": Model(name="mymodel", provider="missing")},
    )
    result = runner.invoke(app, ["mymodel"], obj=config)
    assert result.exit_code == 1
    assert "not found" in result.output


# Ollama error during chat


def test_chat_ollama_error(config_with_model):
    with patch("guided.chat.command.ollama.Client") as mock_client_cls:
        mock_client_cls.return_value.chat.side_effect = Exception("connection refused")
        result = runner.invoke(app, ["llama3"], obj=config_with_model, input="hello\n")
    assert result.exit_code == 1
    assert "Error" in result.output
