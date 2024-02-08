"""Management of versions to help users update."""

from typing import List, Dict
import os
import re
from configparser import ConfigParser
from datetime import datetime


from .utils.common_utils import config_path
from .utils.logging import logger  # pylint: disable=cyclic-import


def get_updated_versions(current_version: str) -> List[Dict]:
    """Get latest version from PyPI."""
    # pylint: disable=import-outside-toplevel
    import requests  # type: ignore
    from packaging.version import Version

    url = "https://api.github.com/repos/redbrick-ai/redbrick-sdk/releases"
    try:
        releases = requests.get(url, timeout=30).json()
        releases = [
            (Version(release["tag_name"]), release)
            for release in releases
            if isinstance(release, dict) and release.get("tag_name")
        ]
        releases.sort(key=lambda release: release[0], reverse=True)
    except Exception:  # pylint: disable=broad-except
        return []

    current_release = Version(current_version)
    updated_versions = []

    for release in releases:
        if release[0] > current_release and (
            current_release.is_prerelease or not release[0].is_prerelease
        ):
            updated_versions.append(release[1])

    return updated_versions


def version_check(current_version: str, check_version: bool) -> None:
    """Check if current installed version of the SDK is up to date with latest pypi release."""
    if not check_version:
        return

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
        updated_versions = get_updated_versions(current_version)
        latest_version = re.sub(
            r"^v",
            "",
            updated_versions[0]["tag_name"] if updated_versions else current_version,
        )
        # Comparing with current installed version
        if latest_version != current_version:
            warn = (
                "You are using version '%s' of the SDK. However, version '%s' is available!\n"
                + "Please update as soon as possible to get the latest features and bug fixes.\n"
                + "You can use 'python -m pip install redbrick-sdk==%s' to get the latest version."
            )
            logger.warning(warn, current_version, latest_version, latest_version)
            logger.info("\nCHANGELOG:\n" + "=" * 20 + "\n")
            for updated_version in updated_versions:
                version_name: str = updated_version["name"]
                version_log: str = updated_version["body"]

                version_log = re.sub(
                    r" by @[\w-]+ in https://github.com/redbrick-ai/redbrick-sdk/pull/\d+",
                    "",
                    re.sub(
                        r".*: https://github.com/redbrick-ai/redbrick-sdk/compare/.*",
                        "",
                        version_log,
                    ),
                ).strip()
                logger.info(
                    f"{version_name}\n{'-' * len(version_name)}\n{version_log}\n\n"
                )

        cache_config["version"]["latest_version"] = latest_version
        cache_config["version"]["last_checked"] = str(current_timestamp)
        update_cache = True

    if update_cache:
        with open(cache_file, "w", encoding="utf-8") as file_:
            cache_config.write(file_)
