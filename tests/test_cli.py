import yaml
import guided
from typer.testing import CliRunner

from guided.cli import app

runner = CliRunner()


def test_version_output(tmp_path, monkeypatch):
    monkeypatch.setenv("GUIDED_HOME_PATH", str(tmp_path))
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert guided.__version__ in result.output


def test_validate_config_callback_exits_on_invalid_config(tmp_path, monkeypatch):
    monkeypatch.setenv("GUIDED_HOME_PATH", str(tmp_path))
    data = {
        "providers": {"ollama": {"name": "ollama", "base_url": "http://localhost:11434"}},
        "models": {
            "m1": {"name": "m1", "provider": "ollama", "is_default": True},
            "m2": {"name": "m2", "provider": "ollama", "is_default": True},
        },
        "skills": {},
    }
    (tmp_path / "config.yaml").write_text(yaml.dump(data))
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 1
    assert "Configuration error" in result.output
