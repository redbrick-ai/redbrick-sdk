import pytest
from redbrick.cli.input.api_key import CLIInputAPIKey


class TestCLIInputAPIKey:
    @pytest.fixture
    def cli_input_api_key(self):
        return CLIInputAPIKey(None)

    def test_filtrator(self, cli_input_api_key):
        filtered_entity = cli_input_api_key.filtrator("  test_api_key  ")
        assert filtered_entity == "test_api_key"

    def test_validator_valid(self, cli_input_api_key):
        valid_api_key = "valid_api_key_" + "0" * 29
        assert cli_input_api_key.validator(valid_api_key)

    def test_validator_invalid_length(self, cli_input_api_key):
        invalid_api_key = "invalid_api_key"
        assert not cli_input_api_key.validator(invalid_api_key)

    def test_validator_invalid_characters(self, cli_input_api_key):
        invalid_api_key = "invalid_api_key!"  # contains invalid character
        assert not cli_input_api_key.validator(invalid_api_key)

    def test_get_from_args(self, cli_input_api_key):
        _valid_api_key = "valid_api_key_" + "0" * 29
        cli_input_api_key.entity = _valid_api_key
        assert cli_input_api_key.get() == _valid_api_key
