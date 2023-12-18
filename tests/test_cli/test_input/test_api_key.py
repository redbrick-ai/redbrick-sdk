"""Tests for redbrick.cli.input.api_key."""
import pytest
from redbrick.cli.input.api_key import CLIInputAPIKey


@pytest.mark.unit
def test_filtrator():
    """Test `CLIInputAPIKey.filtrator`"""
    filtered_entity = CLIInputAPIKey(None).filtrator("  test_api_key  ")
    assert filtered_entity == "test_api_key"


@pytest.mark.unit
def test_validator_valid():
    """Test `CLIInputAPIKey.validator`"""
    valid_api_key = "valid_api_key_" + "0" * 29
    assert CLIInputAPIKey(None).validator(valid_api_key)


@pytest.mark.unit
def test_validator_invalid_length():
    """Test `CLIInputAPIKey.validator` with invalid input length"""
    invalid_api_key = "invalid_api_key"
    assert not CLIInputAPIKey(None).validator(invalid_api_key)


@pytest.mark.unit
def test_validator_invalid_characters():
    """Test `CLIInputAPIKey.validator` with invalid characters"""
    invalid_api_key = "invalid_api_key!"  # contains invalid character
    assert not CLIInputAPIKey(None).validator(invalid_api_key)


@pytest.mark.unit
def test_get_from_args():
    """Test `CLIInputAPIKey.get`"""
    _valid_api_key = "valid_api_key_" + "0" * 29
    cli_input_api_key = CLIInputAPIKey(_valid_api_key)
    assert cli_input_api_key.get() == _valid_api_key
