from unittest.mock import patch

import pytest
from deepeval import assert_test
from deepeval.metrics import ToolCorrectnessMetric
from deepeval.test_case import LLMTestCase, ToolCall

from guided.configure.schema import Skill
from guided.skills.executor import execute_tool, skill_to_tool

WEB_SEARCH_SKILL = Skill(
    name="web_search",
    description="Search the web",
    type="web_search",
)

FILE_READ_SKILL = Skill(
    name="file_read",
    description="Read a file",
    type="file_read",
)

UNKNOWN_SKILL = Skill(
    name="custom_tool",
    description="Some unknown tool",
    type="unknown_type",
)


# --- skill_to_tool ---


def test_skill_to_tool_web_search():
    tool = skill_to_tool(WEB_SEARCH_SKILL)
    assert tool is not None
    assert tool["type"] == "function"
    assert tool["function"]["name"] == "web_search"
    assert "query" in tool["function"]["parameters"]["properties"]


def test_skill_to_tool_file_read():
    tool = skill_to_tool(FILE_READ_SKILL)
    assert tool is not None
    assert tool["function"]["name"] == "file_read"
    assert "path" in tool["function"]["parameters"]["properties"]


def test_skill_to_tool_unknown_returns_none():
    assert skill_to_tool(UNKNOWN_SKILL) is None


# --- execute_tool ---


@patch("guided.skills.web_search.DDGS")
def test_execute_web_search_returns_formatted_results(mock_ddgs):
    mock_ddgs.return_value.text.return_value = [
        {"title": "Python language", "href": "https://example.com/python"},
        {"title": "Python snake", "href": "https://example.com/snake"},
    ]

    result = execute_tool(WEB_SEARCH_SKILL, {"query": "python"})

    assert "Python language" in result
    assert "https://example.com/python" in result


@patch("guided.skills.web_search.DDGS")
def test_execute_web_search_no_results(mock_ddgs):
    mock_ddgs.return_value.text.return_value = []

    result = execute_tool(WEB_SEARCH_SKILL, {"query": "xyzzy_nothing"})

    assert result == "No results found."


def test_execute_unknown_skill_returns_error():
    result = execute_tool(UNKNOWN_SKILL, {})
    assert "unknown skill type" in result
    assert "unknown_type" in result


# --- deepeval ToolCorrectnessMetric ---

AVAILABLE_TOOLS = [
    ToolCall(name="web_search", input_parameters={"query": "..."}),
    ToolCall(name="file_read", input_parameters={"path": "..."}),
]


@pytest.mark.with_llm
@patch("guided.skills.web_search.DDGS")
def test_tool_correctness_web_search(mock_ddgs, eval_model):
    mock_instance = mock_ddgs.return_value.__enter__.return_value
    mock_instance.text.return_value = [
        {"title": "Python language", "href": "https://example.com/python"},
    ]

    tool_output = execute_tool(WEB_SEARCH_SKILL, {"query": "python"})

    test_case = LLMTestCase(
        input="Search for python",
        actual_output=tool_output,
        tools_called=[
            ToolCall(
                name="web_search",
                input_parameters={"query": "python"},
                output=tool_output,
            )
        ],
        expected_tools=[
            ToolCall(name="web_search", input_parameters={"query": "python"})
        ],
    )

    assert_test(
        test_case,
        [ToolCorrectnessMetric(available_tools=AVAILABLE_TOOLS, model=eval_model)],
    )


@pytest.mark.with_llm
def test_tool_correctness_wrong_tool_fails(eval_model):
    """ToolCorrectnessMetric should fail when the wrong tool is called."""
    metric = ToolCorrectnessMetric(available_tools=AVAILABLE_TOOLS, model=eval_model)

    test_case = LLMTestCase(
        input="Search for python",
        actual_output="some result",
        tools_called=[
            ToolCall(name="file_read", input_parameters={"path": "/etc/hosts"})
        ],
        expected_tools=[
            ToolCall(name="web_search", input_parameters={"query": "python"})
        ],
    )

    metric.measure(test_case)
    assert metric.score < 1.0
