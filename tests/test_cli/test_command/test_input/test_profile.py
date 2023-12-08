import pytest
from unittest.mock import patch

from redbrick.cli.input import profile


def test_cli_input_params_filtrator():
    handler = profile.CLIInputProfile(entity=None, profiles=[], add=False, default=None)
    assert handler.filtrator(" test ") == "test"


def test_cli_input_params_validator_add_is_false():
    handler = profile.CLIInputProfile(
        entity=None, profiles=["profile1", "invalid@profile"], add=False, default=None
    )
    assert handler.validator("profile1") is True
    assert handler.validator("profile2") is False
    assert handler.validator("invalid@profile") is False
    assert handler.validator("default") is False


def test_cli_input_params_validator_add_is_true():
    handler = profile.CLIInputProfile(
        entity=None, profiles=["profile1"], add=True, default=None
    )
    assert handler.validator("profile1") is False
    assert handler.validator("profile2") is True


def test_cli_input_profile_get_from_args():
    handler = profile.CLIInputProfile(
        entity="profile1", profiles=["profile1"], add=False, default=None
    )
    assert handler.get() == "profile1"


@patch("InquirerPy.prompts.fuzzy.FuzzyPrompt.execute")
def test_cli_input_profile_get_fuzzy_prompt(mock_fuzzy_prompt):
    mock_fuzzy_prompt.return_value = "selected_profile"
    handler = profile.CLIInputProfile(
        entity=None, profiles=["profile1"], add=False, default=None
    )
    assert handler.get() == "selected_profile"


@patch("InquirerPy.prompts.input.InputPrompt.execute")
def test_cli_input_profile_get_input_prompt(mock_input_prompt):
    mock_input_prompt.return_value = "new_profile"
    handler = profile.CLIInputProfile(
        entity=None, profiles=["profile1"], add=True, default=None
    )
    assert handler.get() == "new_profile"


def test_cli_input_profile_get_no_profiles():
    handler = profile.CLIInputProfile(entity=None, profiles=[], add=False, default=None)
    with pytest.raises(ValueError, match="No profiles available"):
        handler.get()
