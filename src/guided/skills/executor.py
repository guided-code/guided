import time
from typing import Callable

from guided.configure.schema import Skill
from guided.skills.schema import SkillExecution


def execute_skill(skill: Skill, **kwargs) -> SkillExecution:
    # Initialize
    exec = SkillExecution(skill=skill)
    exec.status = "pending"
    exec.start_time = time.process_time()

    # Run
    try:
        assert isinstance(skill.handler, Callable), (
            f"Skill(name={skill.name}) handler must be a callable function"
        )
        result = skill.handler(**kwargs)
    except Exception as e:
        exec.status = "error"
        raise e

    # Complete
    exec.end_time = time.process_time()
    exec.status = "complete"
    exec.result = str(result)

    return exec
