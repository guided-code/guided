from unittest.mock import MagicMock, patch

from guided.configure.command import setup_configuration
from guided.configure.config import get_default_config
from guided.configure.schema import Configuration, Model, Provider


def _config_with_model(model_name="existing-model"):
    config = get_default_config()
    config.models[model_name] = Model(name=model_name, provider="ollama", is_default=True)
    return config


def _mock_ollama_response(model_name):
    mock_model = MagicMock()
    mock_model.model = model_name
    mock_response = MagicMock()
    mock_response.models = [mock_model]
    return mock_response


def test_configure_saves_config_when_ollama_unavailable(tmp_path, monkeypatch):
    monkeypatch.setenv("GUIDED_HOME_PATH", str(tmp_path))
    config = get_default_config()
    with patch("guided.configure.command.ollama.Client") as mock_client_cls, \
         patch("guided.configure.command.save_config") as mock_save:
        mock_client_cls.return_value.list.side_effect = Exception("connection refused")
        setup_configuration(config)
    mock_save.assert_called_once()


def test_configure_discovers_and_adds_new_model(tmp_path, monkeypatch):
    monkeypatch.setenv("GUIDED_HOME_PATH", str(tmp_path))
    config = get_default_config()
    with patch("guided.configure.command.ollama.Client") as mock_client_cls, \
         patch("guided.configure.command.save_config") as mock_save:
        mock_client_cls.return_value.list.return_value = _mock_ollama_response("llama3:latest")
        setup_configuration(config)
    assert "llama3:latest" in config.models
    assert config.models["llama3:latest"].is_default is True
    mock_save.assert_called_once()


def test_configure_does_not_duplicate_existing_model(tmp_path, monkeypatch):
    monkeypatch.setenv("GUIDED_HOME_PATH", str(tmp_path))
    config = _config_with_model("llama3:latest")
    initial_count = len(config.models)
    with patch("guided.configure.command.ollama.Client") as mock_client_cls, \
         patch("guided.configure.command.save_config"):
        mock_client_cls.return_value.list.return_value = _mock_ollama_response("llama3:latest")
        setup_configuration(config)
    assert len(config.models) == initial_count


def test_configure_use_default_flag(tmp_path, monkeypatch):
    monkeypatch.setenv("GUIDED_HOME_PATH", str(tmp_path))
    custom_config = Configuration(
        providers={"custom": Provider(name="custom", base_url="http://custom:1234")}
    )
    with patch("guided.configure.command.ollama.Client") as mock_client_cls, \
         patch("guided.configure.command.save_config") as mock_save:
        mock_client_cls.return_value.list.side_effect = Exception("unavailable")
        setup_configuration(custom_config, overwrite_with_default=True)
    saved_config = mock_save.call_args[0][0]
    assert "ollama" in saved_config.providers
    assert "custom" not in saved_config.providers
