"""Tests for redbrick.cli.entity.conf"""
import os.path
from configparser import ConfigParser, MissingSectionHeaderError

import pytest

from redbrick.cli.entity import CLIConfiguration


@pytest.mark.unit
def test_configuration_creation(empty_config_file):
    """Test CLIConfiguration initialization"""
    config = CLIConfiguration(empty_config_file)
    assert isinstance(config, CLIConfiguration)
    assert isinstance(config._conf, ConfigParser)  # pylint: disable=protected-access
    assert config.exists


@pytest.mark.unit
def test_configuration_save_and_load(empty_config_file):
    """Test saving and loading a configuration"""
    config = CLIConfiguration(empty_config_file)
    # Set a section and an option
    config.set_section("TestSection", {"Option1": "Value1"})
    # Save the configuration
    config.save()
    assert os.stat(empty_config_file).st_size > 0

    # Create a new configuration object and check if it reads the saved data
    new_config = CLIConfiguration(empty_config_file)
    section_data = new_config.get_section("TestSection")
    # note: key is always lowercase
    assert section_data == {"option1": "Value1"}
    assert "Option1" not in section_data


@pytest.mark.unit
def test_configuration_get_set_options(empty_config_file):
    """Test getting and setting options"""
    config = CLIConfiguration(empty_config_file)
    # Set an option
    config.set_option("TestSection", "Option1", "Value1")
    config.save()

    # Get the option
    value = config.get_option("TestSection", "Option1")
    assert value == "Value1"


@pytest.mark.unit
def test_configuration_nonexistent_file():
    """Test that the configuration object handles nonexistent files"""
    config = CLIConfiguration("nonexistent_file")
    assert config.exists is False


@pytest.mark.unit
def test_configuration_invalid_file(empty_config_file):
    """Test that the configuration object handles invalid files"""
    with open(empty_config_file, "w", encoding="utf-8") as file:
        file.write("Invalid Config")
    with pytest.raises(MissingSectionHeaderError):
        CLIConfiguration(empty_config_file)
