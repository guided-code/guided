from typing import Dict

from pydantic import BaseModel, Field


class Provider(BaseModel):
    name: str
    base_url: str


class Model(BaseModel):
    name: str
    provider: str
    is_default: bool = False


class GuidedConfig(BaseModel):
    version: str = Field(default="0.0.0")
    providers: Dict[str, Provider] = Field(default_factory=dict)
    models: Dict[str, Model] = Field(default_factory=dict)
