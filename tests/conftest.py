"""
Pytest configuration for guided project.

This module adds custom pytest options and fixtures for testing with LLM capabilities.
"""

import os

import pytest
from deepeval.models import OllamaModel


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add custom command-line options to pytest."""
    parser.addoption(
        "--with-llm",
        action="store_true",
        default=False,
        help="Run tests that require an LLM (e.g., DeepEval tests). Skips by default.",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "with_llm: mark test as requiring an LLM (disabled by default)"
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list) -> None:
    """Skip LLM tests unless --with-llm is provided."""
    if not config.getoption("--with-llm"):
        skip_llm = pytest.mark.skip(reason="use --with-llm to run LLM-dependent tests")
        for item in items:
            if "with_llm" in item.keywords:
                item.add_marker(skip_llm)


@pytest.fixture(scope="session")
def eval_model():
    """Return an OllamaModel for deepeval evaluation.

    Requires the PYTEST_LOCAL_MODEL_NAME environment variables
    and are skipped when the variable(s) is absent.
    """
    model_name = os.environ.get("PYTEST_LOCAL_MODEL_NAME")
    base_url = os.environ.get("PYTEST_LOCAL_MODEL_BASE_URL", "http://localhost:11434")

    if not model_name:
        pytest.skip("PYTEST_LOCAL_MODEL_NAME not set — skipping LLM eval tests")

    return OllamaModel(
        model=model_name,
        base_url=base_url,
        temperature=0,
    )
