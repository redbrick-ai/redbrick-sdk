"""Tests for redbrick.cli.entity.cache"""
import os
from datetime import datetime

import pytest

from redbrick.cli.entity import CLICache


@pytest.mark.unit
def test_cache_initialization(mock_conf):
    """Assert that cache object and cache dir exist"""
    # pylint: disable=protected-access
    conf, cache_dir = mock_conf
    cli_cache = CLICache(cache_dir, conf)
    assert cli_cache.exists is False
    assert os.path.isfile(conf._conf_file)


@pytest.mark.unit
def test_cache_path(cli_cache):
    """Test `CLICache.cache_path`"""
    # pylint: disable=protected-access
    path = cli_cache.cache_path("test", "entity", fixed_cache=True)
    assert path == os.path.join(cli_cache._cache_dir, "sdk-cache", "test", "entity")

    path = cli_cache.cache_path("test", "entity", fixed_cache=False)
    assert path.endswith(os.path.join(cli_cache._cache_name, "test", "entity"))


@pytest.mark.unit
def test_get_and_set_object(cli_cache):
    """Test get and set object"""
    entity_name = "test_entity"

    # Set an object in the cache
    test_object = {"key": "value"}
    cli_cache.set_object(entity_name, test_object)

    # Get the object
    cached_object = cli_cache.get_object(entity_name)
    assert cached_object == test_object


@pytest.mark.unit
def test_get_nonexistent_object(cli_cache):
    """Test get nonexistent object"""
    entity_name = "test_entity"
    assert cli_cache.get_object(entity_name) is None


@pytest.mark.unit
def test_get_object_expired(cli_cache):
    """Test getting expired object from cache"""
    entity_name = "expired_entity"

    # Set an object in the cache
    test_object = {"key": "value"}
    cli_cache.set_object(entity_name, test_object, save_conf=False)

    # Manually set an old timestamp to simulate an expired cache
    # pylint: disable=protected-access
    old_timestamp = int(datetime.utcnow().timestamp()) - (cli_cache.CACHE_LIFETIME + 1)
    cli_cache._conf.set_option(entity_name, "refresh", str(old_timestamp))
    cli_cache._conf.save()

    # Cache should be considered expired
    assert cli_cache.get_object(entity_name) is None


@pytest.mark.unit
def test_get_data(cli_cache):
    """Test getting data from cache"""
    cache_name = "test_cache_data"
    cache_hash = cli_cache.set_data(cache_name, {"key": "value"})
    data = cli_cache.get_data(cache_name, cache_hash)
    assert data == {"key": "value"}


@pytest.mark.unit
def test_remove_data(cli_cache):
    """Test removing data from cache"""
    cache_name = "test_remove_data"
    cli_cache.set_data(cache_name, {"key": "value"})
    assert os.path.isfile(cli_cache.cache_path(cache_name))

    cli_cache.remove_data(cache_name)
    assert not os.path.isfile(cli_cache.cache_path(cache_name))


@pytest.mark.unit
def test_get_entity(cli_cache):
    """Test getting an entity from cache"""
    entity_name = "test_entity.json"
    entity_data = {"key": "value"}
    cli_cache.set_entity(entity_name, entity_data)

    entity = cli_cache.get_entity(entity_name)
    assert entity == entity_data


@pytest.mark.unit
def test_set_entity(cli_cache):
    """Test setting entity in cache"""
    # pylint: disable=protected-access
    entity_name = "test_set_entity.json"
    entity_data = {"key": "value"}
    cli_cache.set_entity(entity_name, entity_data)
    entity_path = cli_cache.cache_path(*cli_cache._task_path(entity_name))
    assert os.path.isfile(entity_path)

    with open(entity_path, "r", encoding="utf-8") as file:
        stored_data = file.read()

    assert stored_data == '{"key":"value"}'


@pytest.mark.unit
def test_remove_entity(cli_cache):
    """Test removing an entity from cache"""
    # pylint: disable=protected-access
    entity_name = "test_remove_entity.json"
    entity_data = {"key": "value"}
    cli_cache.set_entity(entity_name, entity_data)

    entity_path = cli_cache.cache_path(*cli_cache._task_path(entity_name))
    assert os.path.isfile(entity_path)

    cli_cache.remove_entity(entity_name)
    assert not os.path.isfile(entity_path)


@pytest.mark.skip("This feature needs to be reworked")
@pytest.mark.unit
def test_clear_cache(cli_cache):
    """Test `CLICache.clear_cache`"""
    # pylint: disable=protected-access
    cache_name = "test_cache_data"
    cli_cache.set_data(cache_name, {"key": "value"})

    cli_cache.clear_cache()
    assert not os.path.exists(cli_cache.cache_path(cache_name))
    assert os.path.exists(cli_cache.cache_path(cli_cache._cache_name))
    assert os.path.exists(cli_cache.cache_path(cli_cache._fixed_cache_name))


@pytest.mark.unit
def test_clear_all_caches(cli_cache):
    """Test `CLICache.clear_cache` clears all caches with `all_caches=True`"""
    # pylint: disable=protected-access
    cache_name = "test_cache_data"
    fixed_cache_name = os.path.join(
        "sdk-cache", cli_cache._cache_name, "test_cache_data"
    )
    cli_cache.set_data(cache_name, {"key": "value"})

    cli_cache.clear_cache(all_caches=True)
    assert not os.path.exists(cli_cache.cache_path(cache_name))
    assert not os.path.exists(cli_cache.cache_path(fixed_cache_name, fixed_cache=True))
    assert not os.path.exists(cli_cache.cache_path(cli_cache._cache_name))


@pytest.mark.unit
def test_init_cache_with_existing_config_file(mock_conf):
    """Test cache init with existing conf"""
    # pylint: disable=protected-access
    conf, cache_dir = mock_conf
    CLICache(cache_dir, conf)
    cache_name = conf.get_option("cache", "name")

    cache = CLICache(cache_dir, conf)
    assert os.path.isfile(conf._conf_file)
    assert cache._cache_name == cache_name


@pytest.mark.unit
def test_init_cache_clears_cache_when_version_differs(mock_conf):
    """Assert that cache is cleared with a different SDK version"""
    # pylint: disable=protected-access
    conf, cache_dir = mock_conf
    cli_cache = CLICache(cache_dir, conf)
    cli_cache._cache_name = "old-cache-version"
    cli_cache._conf.set_option("cache", "name", cli_cache._cache_name)
    cli_cache._conf.save()

    cli_cache.set_data("test_cache_data", {"key": "value"})
    cache_path = os.path.join(cli_cache._cache_dir, cli_cache._cache_name)
    assert os.path.isdir(cache_path)

    new_cli_cache = CLICache(cache_dir, conf)
    assert os.path.exists(cache_path) is False
    assert new_cli_cache._cache_name != "old-cache-version"
