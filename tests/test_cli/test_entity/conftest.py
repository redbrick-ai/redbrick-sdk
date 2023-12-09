"""Pytest fixtures for tests in tests.test_cli.test_entity"""
import pytest

from redbrick.cli.entity import CLICredentials, CLIConfiguration, CLICache


@pytest.fixture(scope="function")
def empty_config_file(tmpdir) -> str:
    """Create a temporary directory and file for testing"""
    file_path = tmpdir / "test_config"
    with open(file_path, "w", encoding="utf-8") as file:
        file.write("")

    return file.name


@pytest.fixture
def mock_creds_instance(
    empty_config_file,  # pylint: disable=redefined-outer-name
) -> CLICredentials:
    """Prepare a mock CLICredentials instance"""
    creds = CLICredentials(empty_config_file)
    creds.add_profile(
        "test_profile", "test_api_key", "test_org_id", "https://test.api.com"
    )
    return creds


@pytest.fixture
def mock_conf(tmpdir):
    """Prepare a test CLIConfiguration object"""
    conf_path = tmpdir / "config"
    cache_dir = tmpdir / "cache"
    with open(conf_path, "w", encoding="utf-8") as file:
        file.write("")
    conf = CLIConfiguration(conf_path)
    return conf, cache_dir


@pytest.fixture
def cli_cache(mock_conf):  # pylint: disable=redefined-outer-name
    """Prepare a test CLICache object"""
    conf, cache_dir = mock_conf
    return CLICache(cache_dir, conf)
