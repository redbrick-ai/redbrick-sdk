"""Management of versions to help users update."""

import os
from configparser import ConfigParser
from datetime import datetime

from packaging.version import Version

from .utils.common_utils import config_path
from .utils.logging import logger  # pylint: disable=cyclic-import


def get_latest_version(current_version: str) -> str:
    """Get latest version from PyPI."""
    # pylint: disable=import-outside-toplevel
    import requests  # type: ignore

    url = "https://pypi.org/pypi/redbrick-sdk/json"
    data = requests.get(url, timeout=30).json()
    versions = sorted(map(Version, data["releases"].keys()), reverse=True)
    for version in versions:
        if not version.is_prerelease:
            return str(version)
    return current_version


def version_check(current_version: str) -> None:
    """Check if current installed version of the SDK is up to date with latest pypi release."""
    logger.debug(f"SDK version: {current_version}")
    cache_file = os.path.join(config_path(), "version")
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)

    cache_config = ConfigParser()
    cache_config.read(cache_file)

    update_cache = False

    if (
        "version" not in cache_config
        or "current_version" not in cache_config["version"]
        or cache_config["version"]["current_version"] != current_version
    ):
        cache_config["version"] = {"current_version": current_version}
        update_cache = True

    current_timestamp = int(datetime.now().timestamp())

    if (
        "latest_version" not in cache_config["version"]
        or "last_checked" not in cache_config["version"]
        or current_timestamp - int(cache_config["version"]["last_checked"]) > 86400
    ):
        latest_version = get_latest_version(current_version)
        # Comparing with current installed version
        if Version(current_version) < Version(latest_version):
            warn = (
                "You are using version '%s' of the SDK. However, version '%s' is available!\n"
                + "Please update as soon as possible to get the latest features and bug fixes.\n"
                + "You can use 'python -m pip install redbrick-sdk==%s' to get the latest version."
            )
            logger.warning(warn, current_version, latest_version, latest_version)

        cache_config["version"]["latest_version"] = latest_version
        cache_config["version"]["last_checked"] = str(current_timestamp)
        update_cache = True

    if update_cache:
        with open(cache_file, "w", encoding="utf-8") as file_:
            cache_config.write(file_)
