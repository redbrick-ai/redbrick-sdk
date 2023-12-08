"""Tests for redbrick.cli.input.select"""
import pytest

from redbrick.cli.input.select import CLIInputSelect


@pytest.mark.unit
def test_filtrator():
    """Test CLIInputSelect filtrator"""
    cli_input_select = CLIInputSelect(None, "test", ["1", "2", "3"])
    result = cli_input_select.filtrator("  2 ")
    assert result == "2"


@pytest.mark.unit
def test_validator_options():
    """Test CLIInputSelect validator"""
    cli_input_select = CLIInputSelect(None, "test", ["1", "2", "3"])
    result = cli_input_select.validator("2")
    assert result is True


@pytest.mark.unit
def test_validator_options_false():
    """Test CLIInputSelect validator with input not part of options"""
    cli_input_select = CLIInputSelect(None, "test", ["1", "2", "3"])
    result = cli_input_select.validator("4")
    assert result is False


@pytest.mark.unit
def test_validator_dict_options():
    """Test CLIInputSelect validator with input in options"""
    cli_input_select = CLIInputSelect(None, "test", [{"name": "a"}, {"name": "b"}])
    result = cli_input_select.validator("b")
    assert result is True


@pytest.mark.unit
def test_validator_dict_options_false():
    """Test CLIInputSelect validator with input not in options"""
    cli_input_select = CLIInputSelect(None, "test", [{"name": "a"}, {"name": "b"}])
    result = cli_input_select.validator("c")
    assert result is False


@pytest.mark.unit
def test_get_from_args():
    """Test `CLIInputSelect.get` from args"""
    cli_input_select = CLIInputSelect("2", "test", ["1", "2", "3"])
    result = cli_input_select.get()
    assert result == "2"


@pytest.mark.unit
def test_get_from_prompt(mock_fuzzy_executor):
    """Test `CLIInputSelect.get` from prompt"""
    mock_fuzzy_executor.return_value = "2"
    cli_input_select = CLIInputSelect(None, "test", ["1", "2", "3"])
    result = cli_input_select.get()
    assert result == "2"


@pytest.mark.unit
def test_get_from_prompt_no_options():
    """Test `CLIInputSelect.get` with no options"""
    cli_input_select = CLIInputSelect(None, "test", [])
    with pytest.raises(ValueError, match="No test available"):
        cli_input_select.get()
