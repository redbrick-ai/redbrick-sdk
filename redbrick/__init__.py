"""
Initialize RedBrick package.

Derek Lukacs, 2020
"""

from .client import RedBrickClient
import redbrick.api
import redbrick.logging
from typing import Optional

# import redbrick.base
import redbrick.client
import redbrick.labelset
import redbrick.remote_label
import redbrick.export


def init(api_key: str, url: Optional[str] = None) -> None:
    """Initialize package state."""
    RedBrickClient(api_key, url)
