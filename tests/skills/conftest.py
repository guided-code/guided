import os

import pytest
from deepeval.models import OllamaModel

GUIDED_EVAL_MODEL_ENV = "GUIDED_EVAL_MODEL"


@pytest.fixture(scope="session")
def ollama_model():
    """Return an OllamaModel for deepeval evaluation.

    Requires the GUIDED_EVAL_MODEL environment variable to be set to an
    Ollama model name (e.g. ``llama3.2``).  Tests that depend on this
    fixture are skipped when the variable is absent.
    """
    model_name = os.environ.get(GUIDED_EVAL_MODEL_ENV)
    if not model_name:
        pytest.skip(f"{GUIDED_EVAL_MODEL_ENV} not set — skipping LLM eval tests")
    return OllamaModel(model=model_name)
