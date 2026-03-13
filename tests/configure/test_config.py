import os

import pytest
import yaml

from guided.configure.config import (
    config_exists,
    get_default_config,
    get_guided_home,
    load_config,
    save_config,
)
from guided.configure.schema import Configuration, Model, Provider


def test_get_guided_home_default(monkeypatch):
    monkeypatch.delenv("GUIDED_HOME_PATH", raising=False)
    result = get_guided_home()
    assert result.name == ".guided"


def test_get_guided_home_from_env(tmp_path, monkeypatch):
    monkeypatch.setenv("GUIDED_HOME_PATH", str(tmp_path))
    result = get_guided_home()
    assert result == tmp_path


def test_get_default_config():
    config = get_default_config()
    assert "ollama" in config.providers
    assert config.providers["ollama"].base_url == "http://localhost:11434"
    assert config.models == {}
    assert config.skills == {}


def test_config_exists_false(tmp_path, monkeypatch):
    monkeypatch.setenv("GUIDED_HOME_PATH", str(tmp_path))
    assert config_exists() is False


def test_config_exists_true(tmp_path, monkeypatch):
    monkeypatch.setenv("GUIDED_HOME_PATH", str(tmp_path))
    (tmp_path / "config.yaml").touch()
    assert config_exists() is True


def test_load_config_returns_default_when_no_file(tmp_path, monkeypatch):
    monkeypatch.setenv("GUIDED_HOME_PATH", str(tmp_path))
    config = load_config()
    assert "ollama" in config.providers
    assert config.models == {}


def test_load_config_loads_from_yaml(tmp_path, monkeypatch):
    monkeypatch.setenv("GUIDED_HOME_PATH", str(tmp_path))
    data = {
        "version": "1.0.0",
        "providers": {
            "local": {"name": "local", "base_url": "http://localhost:9999"}
        },
        "models": {},
        "skills": {},
    }
    (tmp_path / "config.yaml").write_text(yaml.dump(data))
    config = load_config()
    assert "local" in config.providers
    assert config.providers["local"].base_url == "http://localhost:9999"
    assert config.version == "1.0.0"


def test_save_config_writes_yaml(tmp_path, monkeypatch):
    monkeypatch.setenv("GUIDED_HOME_PATH", str(tmp_path))
    config = get_default_config()
    save_config(config)
    config_path = tmp_path / "config.yaml"
    assert config_path.exists()
    with config_path.open() as f:
        data = yaml.safe_load(f)
    assert "providers" in data
    assert "ollama" in data["providers"]


def test_save_and_reload_config_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("GUIDED_HOME_PATH", str(tmp_path))
    config = Configuration(
        providers={"test": Provider(name="test", base_url="http://test:1234")},
        models={"m1": Model(name="m1", provider="test", is_default=True)},
    )
    save_config(config)
    loaded = load_config()
    assert "test" in loaded.providers
    assert loaded.providers["test"].base_url == "http://test:1234"
    assert "m1" in loaded.models
    assert loaded.models["m1"].is_default is True


def test_load_config_handles_empty_yaml(tmp_path, monkeypatch):
    monkeypatch.setenv("GUIDED_HOME_PATH", str(tmp_path))
    (tmp_path / "config.yaml").write_text("")
    config = load_config()
    assert isinstance(config, Configuration)
