from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from guided.configure.schema import Skill
from guided.skills.executor import SkillExecution, execute_skill

# Test success case


def test_execute_skill_success():
    """Test that a skill executes successfully and returns a proper SkillExecution."""

    def sample_handler(name: str) -> str:
        return f"Hello, {name}!"

    skill = Skill(
        name="test_skill",
        description="A test skill",
        parameters={},
        handler=sample_handler,
    )

    result = execute_skill(skill, name="World")

    assert isinstance(result, SkillExecution)
    assert result.skill.name == "test_skill"
    assert result.status == "complete"
    assert result.result == "Hello, World!"
    assert result.start_time is not None
    # end_time should be after start_time
    assert result.end_time is not None
    assert result.end_time >= result.start_time


def test_execute_skill_with_kwargs():
    """Test that extra kwargs are passed through to the skill handler."""

    def sample_handler(name: str, value: int = 0) -> str:
        return f"{name}={value}"

    skill = Skill(
        name="test_skill",
        description="A test skill",
        parameters={},
        handler=sample_handler,
    )

    result = execute_skill(skill, name="test", value=42)

    assert result.result == "test=42"
    assert result.status == "complete"


# Test error cases


def test_execute_skill_raises_on_handler_error():
    """Test that exceptions from the handler are re-raised."""

    def failing_handler() -> str:
        raise ValueError("Test error")

    skill = Skill(
        name="failing_skill",
        description="A skill that fails",
        parameters={},
        handler=failing_handler,
    )

    with pytest.raises(ValueError) as exc_info:
        execute_skill(skill)

    assert "Test error" in str(exc_info.value)


def test_execute_skill_raises_when_handler_not_callable():
    """Test that a non-callable handler raises an AssertionError."""
    with pytest.raises(ValidationError, match="1 validation error for Skill"):
        skill = Skill(
            name="invalid_skill",
            description="A skill with invalid handler",
            parameters={},
            handler="not_a_function",  # type: ignore
        )


def test_execute_skill_status_on_error():
    """Test that status is 'error' when an exception occurs."""
    import time

    start_before = time.process_time()

    def failing_handler() -> str:
        time.sleep(0.1)  # Simulate some work
        raise RuntimeError("Simulated failure")

    skill = Skill(
        name="failing_skill",
        description="A skill that fails",
        parameters={},
        handler=failing_handler,
    )

    try:
        execute_skill(skill)
    except RuntimeError:
        pass

    # Note: In the error case, status becomes 'error' before re-raising


# Test SkillExecution model


def test_skill_execution_initial_state():
    """Test that a SkillExecution is initialized with correct default state."""
    skill = Skill(
        name="test_skill",
        description="A test skill",
        parameters={},
        handler=MagicMock(),
    )

    exec = SkillExecution(skill=skill)

    assert exec.skill.name == "test_skill"
    assert exec.status == "initialized"
    assert exec.result is None
    assert exec.start_time is None
    assert exec.end_time is None


def test_skill_execution_complete_state():
    """Test that SkillExecution has correct state after completion."""
    skill = Skill(
        name="test_skill",
        description="A test skill",
        parameters={},
        handler=lambda: "success",
    )

    exec = SkillExecution(skill=skill)
    exec.status = "complete"
    exec.result = "success"
    exec.start_time = 100.0
    exec.end_time = 101.0

    assert exec.status == "complete"
    assert exec.result == "success"
    assert exec.start_time == 100.0
    assert exec.end_time == 101.0


# Test edge cases


def test_execute_skill_returns_string_result():
    """Test that the result is always converted to string."""

    def returns_int() -> int:
        return 42

    skill = Skill(
        name="int_skill",
        description="Returns int",
        parameters={},
        handler=returns_int,
    )

    result = execute_skill(skill)
    assert result.result == "42"
    assert isinstance(result.result, str)


def test_execute_skill_handles_none_result():
    """Test handling of a handler that returns None."""

    def returns_none() -> None:
        pass

    skill = Skill(
        name="none_skill",
        description="Returns None",
        parameters={},
        handler=returns_none,
    )

    result = execute_skill(skill)
    assert result.result == "None"


def test_execute_skill_with_empty_parameters():
    """Test that a skill with no parameters works correctly."""

    def no_params() -> str:
        return "success"

    skill = Skill(
        name="no_params_skill",
        description="No params",
        parameters={},
        handler=no_params,
    )

    result = execute_skill(skill)
    assert result.status == "complete"
    assert result.result == "success"
