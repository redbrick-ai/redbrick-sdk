"""Management of versions to help users update."""

import os
from configparser import ConfigParser
from datetime import datetime

from distutils.version import StrictVersion
from .utils.logging import print_warning  # pylint: disable=cyclic-import


def get_latest_version() -> str:
    """Get latest version from PyPI."""
    # pylint: disable=import-outside-toplevel
    import requests

    url = "https://pypi.org/pypi/redbrick-sdk/json"
    data = requests.get(url).json()
    versions = list(data["releases"].keys())
    versions.sort(key=StrictVersion)
    return str(versions[-1])


def version_check(current_version: str) -> None:
    """Check if current installed version of the SDK is up to date with latest pypi release."""
    cache_file = os.path.join(os.path.expanduser("~"), ".redbrickai", "version")
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
        latest_version = get_latest_version()
        # Comparing with current installed version
        if current_version != latest_version:
            warn = (
                "You are using version '{}' of the SDK. However, version '{}' is available!\n"
                + "Please update as soon as possible to get the latest features and bug fixes.\n"
                + "You can use 'python -m pip install --upgrade redbrick-sdk'"
                + " to get the latest version."
            )
            print_warning(warn.format(current_version, latest_version))

        cache_config["version"]["latest_version"] = latest_version
        cache_config["version"]["last_checked"] = str(current_timestamp)
        update_cache = True

    if update_cache:
        with open(cache_file, "w", encoding="utf-8") as file_:
            cache_config.write(file_)
