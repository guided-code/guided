import os
from pathlib import Path
from typing import Optional

import yaml

import guided
from guided.configure.schema import Configuration, Provider

DEFAULT_GUIDED_HOME_PATH = Path.home() / ".guided"
CONFIG_FILE_NAME = "config.yaml"
OLLAMA_PROVIDER = Provider(name="ollama", base_url="http://localhost:11434")


def get_guided_home() -> Path:
    env_home = os.environ.get("GUIDED_HOME_PATH", str(DEFAULT_GUIDED_HOME_PATH))
    return Path(env_home)


def get_default_config() -> Configuration:
    return Configuration(
        version=guided.__version__,
        providers={"ollama": OLLAMA_PROVIDER},
        skills={},
    )


def ensure_guided_home() -> Path:
    home = get_guided_home()
    home.mkdir(parents=True, exist_ok=True)
    return home


def config_exists() -> bool:
    return (get_guided_home() / CONFIG_FILE_NAME).exists()


def load_config() -> Configuration:
    home = ensure_guided_home()
    config_path = home / CONFIG_FILE_NAME

    # Initialize with default configuration
    if not config_path.exists():
        return get_default_config()

    with config_path.open() as f:
        data = yaml.safe_load(f) or {}

    return Configuration(**data)


def save_config(config: Configuration) -> None:
    home = ensure_guided_home()
    config_path = home / CONFIG_FILE_NAME

    with config_path.open("w") as f:
        yaml.dump(config.model_dump(), f, default_flow_style=False)


def load_agents_md() -> Optional[str]:
    """Load AGENTS.md from current directory or workspace, if it exists.

    Checks in order:
    1. Current directory's AGENTS.md
    2. .workspace/AGENTS.md (in workspace root)
    3. .workspace/context/AGENTS.md (in workspace context folder)
    """
    # Check current directory first
    current_agents = Path("AGENTS.md")
    if current_agents.exists():
        return current_agents.read_text().strip()

    # Check workspace locations
    workspace = Path(".workspace")
    if workspace.is_dir():
        # Check workspace root
        workspace_agents = workspace / "AGENTS.md"
        if workspace_agents.exists():
            return workspace_agents.read_text().strip()

        # Check workspace context folder
        context_agents = workspace / "context" / "AGENTS.md"
        if context_agents.exists():
            return context_agents.read_text().strip()

    return None
