"""Tests for redbrick.cli.input.number."""
import pytest
from redbrick.cli.input import number


@pytest.mark.unit
def test_filtrator():
    """Test `CLIInputNumber.filtrator`"""
    cli_input_number = number.CLIInputNumber(None, "test")
    result = cli_input_number.filtrator(" 42 ")
    assert result == "42"


@pytest.mark.unit
def test_validator_valid():
    """Test `CLIInputNumber.filtrator`"""
    cli_input_number = number.CLIInputNumber(None, "test")
    result = cli_input_number.validator("42")
    assert result is True


@pytest.mark.unit
def test_validator_invalid():
    """Test `CLIInputNumber.validator`"""
    cli_input_number = number.CLIInputNumber(None, "test")
    result = cli_input_number.validator("not_a_number")
    assert result is False


@pytest.mark.unit
def test_validator_invalid_float():
    """Test `CLIInputNumber.validator`"""
    cli_input_number = number.CLIInputNumber(None, "test")
    assert cli_input_number.validator("453.65") is False


@pytest.mark.unit
def test_get_from_args(mock_input_executor):
    """Test `CLIInputNumber.get` from args"""
    mock_input_executor.return_value = "42"
    input_handler = number.CLIInputNumber("42", "Test")
    result = input_handler.get()
    assert result == "42"
    mock_input_executor.assert_not_called()


@pytest.mark.unit
def test_get_from_input_prompt(mock_input_executor):
    """Test `CLIInputNumber.get` from input"""
    mock_input_executor.return_value = "42"
    input_handler = number.CLIInputNumber(None, "Test")
    result = input_handler.get()
    assert result == "42"
    mock_input_executor.assert_called_once()
