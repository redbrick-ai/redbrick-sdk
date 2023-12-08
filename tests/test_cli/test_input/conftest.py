"""Pytest fixtures for tests.test_cli.test_input"""
from unittest.mock import patch

import pytest


@pytest.fixture
def mock_input_executor():
    """Prepare a mock input prompt"""
    with patch("InquirerPy.prompts.input.InputPrompt.execute") as mock_execute:
        with patch("InquirerPy.prompts.input.PromptSession"):
            yield mock_execute
