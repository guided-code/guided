from datetime import datetime, timezone

from pydantic import BaseModel, Field


class WorkspaceConfig(BaseModel):
    name: str
    version: str = Field(default="0.0.1")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
