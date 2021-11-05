"""Management of versions to help users update."""

import os

from distutils.version import StrictVersion
import requests
import redbrick
from .logging import print_warning  # pylint: disable=cyclic-import


def version_check() -> None:
    """Check if current installed version of the SDK is up to date with latest pypi release."""
    # Getting latest version on pypi
    url = "https://pypi.org/pypi/redbrick-sdk/json"
    data = requests.get(url).json()
    versions = list(data["releases"].keys())
    versions.sort(key=StrictVersion)
    latest_version = versions[-1]
    # Comparing with current installed version
    with open(
        os.path.join(os.path.dirname(redbrick.__file__), "VERSION"),
        "r",
        encoding="utf-8",
    ) as file_:
        curr_version = file_.read().strip()
    if curr_version != latest_version:
        warn = (
            "You are using version '{}' of the SDK. However, version '{}' is available!\n"
            + "Please update as soon as possible to get the latest features and bug fixes.\n"
            + "You can use 'python -m pip install --upgrade redbrick-sdk'"
            + " to get the latest version."
        )
        print_warning(warn.format(curr_version, latest_version))
