from typing import Dict

from pydantic import BaseModel, Field, model_validator


class Provider(BaseModel):
    name: str
    base_url: str


class Model(BaseModel):
    name: str
    provider: str
    is_default: bool = False


class Configuration(BaseModel):
    version: str = Field(default="0.0.0")
    providers: Dict[str, Provider] = Field(default_factory=dict)
    models: Dict[str, Model] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_single_default(self) -> "Configuration":
        defaults = [key for key, model in self.models.items() if model.is_default]
        if len(defaults) > 1:
            raise ValueError(
                f"Only one model can be marked as default, but found: {', '.join(defaults)}"
            )
        return self
