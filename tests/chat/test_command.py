import os
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest
import typer
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase
from typer.testing import CliRunner

from guided.chat.command import run_chat
from guided.configure.schema import Configuration, Model, Provider

runner = CliRunner()
app = typer.Typer()


@pytest.fixture(autouse=True)
def mock_workspace_operations():
    with patch("guided.chat.command.initialize_workspace"), \
         patch("guided.chat.command.ChatSession._save_transcript"):
        yield


@app.command()
def chat(
    ctx: typer.Context,
    model: Optional[str] = typer.Argument(default=None, help="Model name to chat with"),
):
    """Chat interactively with a model, or pipe text via stdin for a single response."""
    run_chat(ctx.obj, model=model)


OLLAMA_PROVIDER = Provider(name="ollama", base_url="http://localhost:11434")


@pytest.fixture
def config_with_model():
    return Configuration(
        providers={"ollama": OLLAMA_PROVIDER},
        models={"codellama": Model(name="codellama:34b-python", provider="ollama")},
    )


@pytest.fixture
def config_with_default():
    return Configuration(
        providers={"ollama": OLLAMA_PROVIDER},
        models={"llama3": Model(name="llama3", provider="ollama", is_default=True)},
    )


@pytest.fixture
def empty_config():
    return Configuration()


def _mock_response(content: str) -> MagicMock:
    response = MagicMock()
    response.message.content = content
    response.message.tool_calls = None
    response.message.thinking = False
    return [response]


# No model specified, no default configured


def test_chat_no_model_no_default(empty_config):
    result = runner.invoke(app, [], obj=empty_config)
    assert result.exit_code == 1
    assert "No model specified" in result.output


# No model specified, default configured via is_default=True attribute


def test_chat_uses_default_model(config_with_default):
    with patch("guided.chat.command.ollama.Client") as mock_client_cls:
        mock_client_cls.return_value.chat.return_value = _mock_response("Hello!")
        result = runner.invoke(app, [], obj=config_with_default, input="hi\n\n")
    assert result.exit_code == 0
    assert "Hello!" in result.output
    mock_client_cls.return_value.chat.assert_called_once()


# Model with default=False is not used as default


def test_chat_no_default_when_default_false(config_with_model):
    result = runner.invoke(app, [], obj=config_with_model)
    assert result.exit_code == 1
    assert "No model specified" in result.output


def test_chat_session_reset_session_id():
    from guided.chat.command import ChatSession
    from pathlib import Path

    session = ChatSession(config=MagicMock())
    initial_id = session.session_id
    assert len(initial_id) == 8

    session._transcript_file = Path("/fake/.workspace/transcripts") / f"{initial_id}_datetime.yaml"
    session.reset_session_id()

    new_id = session.session_id
    assert new_id != initial_id
    assert len(new_id) == 8
    assert new_id in str(session._transcript_file)
    assert str(session._transcript_file).endswith(".yaml")


@pytest.mark.with_llm
def test_chat_with_actual_ollama(eval_model):
    """Test chat command against a real Ollama instance if available."""
    config = Configuration(
        providers={"ollama": OLLAMA_PROVIDER},
        models={
            "llm": Model(
                name=os.getenv("PYTEST_LOCAL_MODEL_NAME"),
                provider="ollama",
                is_default=True,
            )
        },
    )

    question = "Who is the current president of the United States of America?"
    result = runner.invoke(app, [], obj=config, input=question)
    test_case = LLMTestCase(
        input=question,
        actual_output=result.output,
        retrieval_context=["Donald Trump serves as the current president of America."],
    )

    answer_relevancy_metric = AnswerRelevancyMetric(model=eval_model)
    answer_relevancy_metric.measure(test_case)
    assert answer_relevancy_metric.score is not None
    assert answer_relevancy_metric.score >= 0.75
