"""Common utility functions."""
import os
import hashlib
from typing import Union


def config_path() -> str:
    """Return package config path."""
    if (
        "VIRTUAL_ENV" in os.environ
        and os.environ["VIRTUAL_ENV"]
        and (conf_dir := os.path.expanduser(os.environ["VIRTUAL_ENV"]))
        and os.path.isdir(conf_dir)
    ):
        return os.path.join(conf_dir, ".redbrickai")

    return os.path.join(os.path.expanduser("~"), ".redbrickai")


def hash_sha256(message: Union[str, bytes]) -> str:
    """Return basic SHA256 of given message."""
    sha256 = hashlib.sha256()
    sha256.update(message.encode() if isinstance(message, str) else message)
    return sha256.hexdigest()
