"""Common utility functions."""
import hashlib
from typing import Union


def hash_sha256(message: Union[str, bytes]) -> str:
    """Return basic SHA256 of given message."""
    sha256 = hashlib.sha256()
    sha256.update(message.encode() if isinstance(message, str) else message)
    return sha256.hexdigest()
