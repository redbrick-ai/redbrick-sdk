"""Tests for redbrick.cli.input.text"""
import pytest

from redbrick.cli.input import text


@pytest.mark.unit
def test_cli_input_text_with_valid_input(mock_input_executor):
    """Test `CLIInputText.get`"""
    mock_input_executor.return_value = "valid_input"
    cli_input_text = text.CLIInputText(None, "Test Input")
    result = cli_input_text.get()
    assert result == "valid_input"
    mock_input_executor.assert_called_once()


@pytest.mark.unit
def test_cli_input_text_with_empty_input():
    """Test `CLIInputText.validator` with empty input"""
    cli_input_text = text.CLIInputText(None, "Test Input", allow_empty=True)
    result = cli_input_text.validator("")
    assert result is True


@pytest.mark.unit
def test_cli_input_text_with_empty_input_disallowed():
    """Test `CLIInputText.validator` with disallowed empty input"""
    cli_input_text = text.CLIInputText(None, "Test Input")
    result = cli_input_text.validator("")
    assert result is False


@pytest.mark.unit
def test_cli_input_text_filtrator():
    """Test `CLIInputText.filtrator`"""
    cli_input_text = text.CLIInputText(None, "Test Input")
    result = cli_input_text.filtrator("  filtered_text  ")
    assert result == "filtered_text"


@pytest.mark.unit
def test_cli_input_text_validator():
    """Test `CLIInputText.validator`"""
    cli_input_text = text.CLIInputText(None, "Test Input")
    assert cli_input_text.validator("valid_input")
    assert cli_input_text.validator("  filtered_text  ")
    assert not cli_input_text.validator("")
    assert not cli_input_text.validator("    ")


@pytest.mark.unit
def test_cli_input_text_from_args():
    """Test `CLIInputText.from_args`"""
    cli_input_text = text.CLIInputText("input_from_args", "Test Input")
    result = cli_input_text.from_args()
    assert result == "input_from_args"
