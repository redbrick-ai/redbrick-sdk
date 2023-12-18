"""Tests for redbrick.cli.input.url."""
import pytest

from redbrick.cli.input.url import CLIInputURL


@pytest.mark.unit
def test_valid_url(mock_input_executor):
    """Test `CLIInputURL.get`"""
    url = "https://example.com"
    mock_input_executor.return_value = url
    input_url = CLIInputURL(None)
    result = input_url.get()
    assert result == url
    mock_input_executor.assert_called_once()


@pytest.mark.unit
def test_invalid_url():
    """Test `CLIInputURL.get` with invalid URL"""
    invalid_url = "invalid_url"
    input_url = CLIInputURL(None)
    result = input_url.validator(invalid_url)
    assert result is False


@pytest.mark.unit
def test_from_args():
    """Test `CLIInputURL.from_args`"""
    url = "https://example.com"
    input_url = CLIInputURL(url)
    result = input_url.from_args()
    assert result == url


@pytest.mark.unit
def test_validator_valid_url():
    """Test `CLIInputURL.validator`"""
    valid_url = "https://example.com"
    input_url = CLIInputURL(None)
    result = input_url.validator(valid_url)
    assert result is True


@pytest.mark.unit
def test_validator_invalid_url():
    """Test `CLIInputURL.validator` with invalid URL"""
    invalid_url = "invalid_url"
    input_url = CLIInputURL(None)
    result = input_url.validator(invalid_url)
    assert result is False


@pytest.mark.unit
def test_filtrator():
    """Test `CLIInputURL.filtrator`"""
    url = " https://example.com "
    input_url = CLIInputURL(None)
    result = input_url.filtrator(url)
    assert result == url.strip().rstrip("/")


@pytest.mark.unit
def test_get(mock_input_executor):
    """Test `CLIInputURL.get`"""
    url = "https://example.com"
    mock_input_executor.return_value = url
    input_url = CLIInputURL(None)
    result = input_url.get()
    assert result == url
