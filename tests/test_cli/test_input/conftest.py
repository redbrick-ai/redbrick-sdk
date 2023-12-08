"""Pytest fixtures for tests.test_cli.test_input"""
from unittest.mock import patch

import pytest


@pytest.fixture
def mock_input_executor():
    """Prepare a mock input prompt"""
    with patch("InquirerPy.prompts.input.InputPrompt.__new__") as mock_prompt:
        yield mock_prompt.return_value.execute
