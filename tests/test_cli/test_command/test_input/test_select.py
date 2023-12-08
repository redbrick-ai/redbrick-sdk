import pytest
from unittest.mock import patch
from redbrick.cli.input.select import CLIInputSelect


def test_filtrator():
    """Test CLIInputSelect filtrator"""
    cli_input_select = CLIInputSelect(None, "test", ["1", "2", "3"])
    result = cli_input_select.filtrator("  2 ")
    assert result == "2"


def test_validator_options():
    """Test CLIInputSelect validator"""
    cli_input_select = CLIInputSelect(None, "test", ["1", "2", "3"])
    result = cli_input_select.validator("2")
    assert result is True


def test_validator_options_false():
    """Test CLIInputSelect validator with input not part of options"""
    cli_input_select = CLIInputSelect(None, "test", ["1", "2", "3"])
    result = cli_input_select.validator("4")
    assert result is False


def test_validator_dict_options():
    """Test CLIInputSelect validator with input in options"""
    cli_input_select = CLIInputSelect(None, "test", [{"name": "a"}, {"name": "b"}])
    result = cli_input_select.validator("b")
    assert result is True


def test_validator_dict_options_false():
    """Test CLIInputSelect validator with input not in options"""
    cli_input_select = CLIInputSelect(None, "test", [{"name": "a"}, {"name": "b"}])
    result = cli_input_select.validator("c")
    assert result is False


def test_get_from_args():
    cli_input_select = CLIInputSelect("2", "test", ["1", "2", "3"])
    result = cli_input_select.get()
    assert result == "2"


def test_get_from_prompt():
    cli_input_select = CLIInputSelect(None, "test", ["1", "2", "3"])
    with patch("InquirerPy.prompts.fuzzy.FuzzyPrompt.execute", return_value="2"):
        result = cli_input_select.get()
        assert result == "2"


def test_get_from_prompt_no_options():
    cli_input_select = CLIInputSelect(None, "test", [])
    with pytest.raises(ValueError, match="No test available"):
        cli_input_select.get()
