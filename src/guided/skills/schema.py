from typing import Any, Optional

from pydantic import BaseModel

from guided.configure.schema import Skill


class SkillExecution(BaseModel):
    """A data object that captures information about invocation of a Skill"""

    skill: Skill
    status: str = "initialized"
    result: Optional[Any] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
