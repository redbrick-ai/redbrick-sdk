from unittest.mock import patch, Mock

import pytest
from redbrick.cli.input import number


class TestCLIInputAPIKey:
    @pytest.fixture
    def cli_input_number(self):
        return number.CLIInputNumber(None, "test")

    def test_filtrator(self, cli_input_number):
        result = cli_input_number.filtrator(" 42 ")
        assert result == "42"

    def test_validator_valid(self, cli_input_number):
        result = cli_input_number.validator("42")
        assert result is True

    def test_validator_invalid(self, cli_input_number):
        result = cli_input_number.validator("not_a_number")
        assert result is False

    def test_validator_invalid_float(self, cli_input_number):
        assert cli_input_number.validator("453.65") is False

    def test_get_from_args(self):
        mock_input_prompt = Mock(return_value="42")
        with patch.object(
            number.InputPrompt, "execute", mock_input_prompt
        ) as mock_input_prompt:
            input_handler = number.CLIInputNumber("42", "Test")
            result = input_handler.get()
            assert result == "42"
            mock_input_prompt.assert_not_called()

    def test_get_from_input_prompt(self):
        mock_input_prompt = Mock(return_value="42")
        with patch.object(number.InputPrompt, "execute", mock_input_prompt):
            input_handler = number.CLIInputNumber(None, "Test")
            result = input_handler.get()
            assert result == "42"
            mock_input_prompt.assert_called_once()
