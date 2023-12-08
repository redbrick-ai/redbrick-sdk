from unittest.mock import patch

import pytest


@pytest.fixture
def mock_input_executor():
    with patch("InquirerPy.prompts.input.InputPrompt.execute") as mock_input_executor:
        yield mock_input_executor
