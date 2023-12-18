"""Tests for redbrick.cli.entity.creds"""
import os
from configparser import MissingSectionHeaderError, ConfigParser

import pytest

from redbrick.cli.entity import CLICredentials


@pytest.mark.unit
def test_cl_credentials_initialization(empty_config_file):
    """Test CLICredentials initialization"""
    creds = CLICredentials(empty_config_file)
    assert isinstance(creds._creds, ConfigParser)  # pylint: disable=protected-access
    assert creds.exists is True
    assert creds.profile_names == []
    os.environ[creds.ENV_VAR] = "test_profile"
    assert creds.selected_profile == "test_profile"
    del os.environ[creds.ENV_VAR]


@pytest.mark.unit
def test_cl_credentials_add_and_get_profile(empty_config_file):
    """Test adding and getting profiles"""
    creds = CLICredentials(empty_config_file)
    creds.add_profile(
        "test_profile", "test_api_key", "test_org_id", "https://test.api.com"
    )
    profile = creds.get_profile("test_profile")
    assert profile == {
        "key": "test_api_key",
        "org": "test_org_id",
        "url": "https://test.api.com",
    }


@pytest.mark.unit
def test_cl_credentials_add_duplicate_profile(mock_creds_instance):
    """Duplicate profiles should throw exceptions"""
    with pytest.raises(Exception, match="Profile already exists"):
        mock_creds_instance.add_profile(
            "test_profile", "new_api_key", "new_org_id", "https://new.api.com"
        )


@pytest.mark.unit
def test_cl_credentials_remove_profile(mock_creds_instance):
    """Test removing profiles"""
    mock_creds_instance.remove_profile("test_profile")
    assert "test_profile" not in mock_creds_instance.profile_names


def test_cl_credentials_remove_nonexistent_profile(mock_creds_instance):
    """Removing nonexistent profile should throw exception"""
    with pytest.raises(Exception, match="Profile does not exist"):
        mock_creds_instance.remove_profile("nonexistent_profile")


@pytest.mark.unit
def test_cl_credentials_set_default_profile(mock_creds_instance):
    """Test setting default profile"""
    mock_creds_instance.add_profile(
        "second_profile", "second_api_key", "second_org_id", "https://second.api.com"
    )
    mock_creds_instance.set_default("second_profile")
    assert mock_creds_instance.selected_profile == "second_profile"


@pytest.mark.unit
def test_cl_credentials_set_default_nonexistent_profile(mock_creds_instance):
    """Setting nonexistent profile as default should throw exception"""
    with pytest.raises(Exception, match="Profile does not exist"):
        mock_creds_instance.set_default("nonexistent_profile")


@pytest.mark.unit
def test_cl_credentials_save_and_load(mock_creds_instance, empty_config_file):
    """Test saving and load profile Credentials"""
    mock_creds_instance.save()
    new_creds_instance = CLICredentials(empty_config_file)
    assert new_creds_instance.exists is True
    assert new_creds_instance.profile_names == ["test_profile"]
    assert new_creds_instance.selected_profile == "test_profile"


@pytest.mark.unit
def test_cl_credentials_save_empty_removes_creds_file(empty_config_file):
    """Test saving empty credentials"""
    creds = CLICredentials(empty_config_file)
    creds.save()
    new_creds_instance = CLICredentials(empty_config_file)
    assert new_creds_instance.exists is False
    assert new_creds_instance.profile_names == []
    with pytest.raises(Exception, match="Credentials file does not exist"):
        assert new_creds_instance.selected_profile == "default"


@pytest.mark.unit
def test_cl_credentials_remove(mock_creds_instance):
    """Test removing Credentials"""
    mock_creds_instance.remove()
    assert not os.path.exists(
        mock_creds_instance._creds_file  # pylint: disable=protected-access
    )


@pytest.mark.unit
def test_credentials_nonexistent_file():
    """Test that the credentials object handles nonexistent files"""
    config = CLICredentials("nonexistent_file")
    assert config.exists is False


@pytest.mark.unit
def test_credentials_invalid_file(empty_config_file):
    """Test that the credentials object handles invalid files"""
    with open(empty_config_file, "w", encoding="utf-8") as file:
        file.write("Invalid Config")
    with pytest.raises(MissingSectionHeaderError):
        CLICredentials(empty_config_file)
