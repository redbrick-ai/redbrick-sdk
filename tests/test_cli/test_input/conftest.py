"""Pytest fixtures for tests.test_cli.test_input"""
import sys
from unittest.mock import patch

import pytest


@pytest.fixture
def mock_input_executor():
    """Prepare a mock input prompt"""
    is_windows = sys.platform == "win32"

    with patch("InquirerPy.prompts.input.InputPrompt.execute") as mock_execute:
        if is_windows:
            with patch("prompt_toolkit.output.defaults.create_output"):
                yield mock_execute
        else:
            yield mock_execute


@pytest.fixture
def mock_fuzzy_executor():
    """Prepare a mock fuzzy prompt"""
    is_windows = sys.platform == "win32"

    with patch("InquirerPy.prompts.fuzzy.FuzzyPrompt.execute") as mock_execute:
        if is_windows:
            with patch("prompt_toolkit.output.defaults.create_output"):
                yield mock_execute
        else:
            yield mock_execute
