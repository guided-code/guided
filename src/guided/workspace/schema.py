from typing import Optional

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class WorkspaceConfig(BaseModel):
    name: str
    workspace_key: Optional[str] = None
    version: str = Field(default="0.0.1")
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
