"""
Initialize RedBrick package.

Derek Lukacs, 2020
"""

from .client import RedBrickClient
import redbrick.api
from typing import Optional

# import redbrick.base
import redbrick.client
import redbrick.labelset
import redbrick.remote_label
import datumaro

# from redbrick.remote_label import RemoteLabel
# from redbrick.entity.remote_label import RemoteLabelTask


def init(api_key: str, url: Optional[str] = None) -> None:
    """Initialize package state."""
    RedBrickClient(api_key, url)
