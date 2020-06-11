"""
Initialize RedBrick package.

Derek Lukacs, 2020
"""

from .client import RedBrickClient
import redbrick.api

# import redbrick.base
import redbrick.client
import redbrick.labelset


def init(api_key: str) -> None:
    """Initialize package state."""
    RedBrickClient(api_key)
