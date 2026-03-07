import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

import guided


DEFAULT_GUIDED_HOME = Path.home() / ".guided"
CONFIG_FILE_NAME = "config.yaml"


class GuidedConfig(BaseModel):
    version: str = Field(default="0.0.0")


def get_guided_home() -> Path:
    env_home = os.environ.get("GUIDED_HOME", str(DEFAULT_GUIDED_HOME))
    return Path(env_home)


def get_default_config() -> GuidedConfig:
    return GuidedConfig(version=guided.__version__)


def ensure_guided_home() -> Path:
    home = get_guided_home()
    home.mkdir(parents=True, exist_ok=True)
    return home


def load_config() -> GuidedConfig:
    home = ensure_guided_home()
    config_path = home / CONFIG_FILE_NAME

    # Initialize with default configuration
    if not config_path.exists():
        return get_default_config()

    with config_path.open() as f:
        data = yaml.safe_load(f) or {}

    return GuidedConfig(**data)


def save_config(config: GuidedConfig) -> None:
    home = ensure_guided_home()
    config_path = home / CONFIG_FILE_NAME

    with config_path.open("w") as f:
        yaml.dump(config.model_dump(), f, default_flow_style=False)
