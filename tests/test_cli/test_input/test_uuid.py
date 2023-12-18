"""Tests for redbrick.cli.input.uuid."""
import pytest

from redbrick.cli.input import CLIInputUUID


@pytest.mark.unit
def test_valid_uuid_input(mock_input_executor):
    """Test `CLIInputUUID.get` with valid UUID"""
    test_uuid = "550e8400-e29b-41d4-a716-446655440000"
    mock_input_executor.return_value = test_uuid
    uuid_input = CLIInputUUID(None, "UUID")
    assert uuid_input.get() == test_uuid


@pytest.mark.unit
def test_validator_valid_uuid_input():
    """Test `CLIInputUUID.get` with valid UUID"""
    test_uuid = "550e8400-e29b-41d4-a716-446655440000"
    uuid_input = CLIInputUUID(None, "UUID")
    assert uuid_input.validator(test_uuid) is True


@pytest.mark.unit
def test_invalid_uuid_input():
    """Test `CLIInputUUID.get` with invalid UUID"""
    uuid_input = CLIInputUUID(None, "UUID")
    assert uuid_input.validator("invalid_uuid") is False


@pytest.mark.unit
def test_empty_uuid_input():
    """Test `CLIInputUUID.get` with empty input"""
    uuid_input = CLIInputUUID(None, "UUID")
    assert uuid_input.validator("") is False
