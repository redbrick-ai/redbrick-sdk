"""Tests for redbrick.cli.input.profile."""
import pytest

from redbrick.cli.input import profile


@pytest.mark.unit
def test_cli_input_params_filtrator():
    """Test `CLIInputProfile.filtrator`"""
    handler = profile.CLIInputProfile(entity=None, profiles=[], add=False, default=None)
    assert handler.filtrator(" test ") == "test"


@pytest.mark.unit
def test_cli_input_params_validator_add_is_false():
    """Test `CLIInputProfile.validator`"""
    handler = profile.CLIInputProfile(
        entity=None, profiles=["profile1", "invalid@profile"], add=False, default=None
    )
    assert handler.validator("profile1") is True
    assert handler.validator("profile2") is False
    assert handler.validator("invalid@profile") is False
    assert handler.validator("default") is False


@pytest.mark.unit
def test_cli_input_params_validator_add_is_true():
    """Test `CLIInputProfile.validator`"""
    handler = profile.CLIInputProfile(
        entity=None, profiles=["profile1"], add=True, default=None
    )
    assert handler.validator("profile1") is False
    assert handler.validator("profile2") is True


@pytest.mark.unit
def test_cli_input_profile_get_from_args():
    """Test `CLIInputProfile.validator`"""
    handler = profile.CLIInputProfile(
        entity="profile1", profiles=["profile1"], add=False, default=None
    )
    assert handler.get() == "profile1"


@pytest.mark.unit
def test_cli_input_profile_get_fuzzy_prompt(mock_fuzzy_executor):
    """Test `CLIInputProfile.get` with add=False"""
    mock_fuzzy_executor.return_value = "selected_profile"
    handler = profile.CLIInputProfile(
        entity=None, profiles=["profile1"], add=False, default=None
    )
    assert handler.get() == "selected_profile"


@pytest.mark.unit
def test_cli_input_profile_get_input_prompt(mock_input_executor):
    """Test `CLIInputProfile.get` with add=True"""
    mock_input_executor.return_value = "new_profile"
    handler = profile.CLIInputProfile(
        entity=None, profiles=["profile1"], add=True, default=None
    )
    assert handler.get() == "new_profile"


@pytest.mark.unit
def test_cli_input_profile_get_no_profiles():
    """Test `CLIInputProfile.get` with no profiles"""
    handler = profile.CLIInputProfile(entity=None, profiles=[], add=False, default=None)
    with pytest.raises(ValueError, match="No profiles available"):
        handler.get()
