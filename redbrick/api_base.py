"""Abstract interface to RedBrick API."""

from typing import List
from abc import ABC, abstractmethod
from redbrick.entity import DataPoint


class RedBrickApiBase(ABC):
    """Abstract interface to RedBrick API."""

    @abstractmethod
    def get_datapoint_ids(self, org_id: str, label_set_name: str) -> List[str]:
        """Get a list of datapoint ids in labelset."""

    @abstractmethod
    def get_datapoint(self, org_id: str, label_set_name: str, dp_id: str) -> DataPoint:
        """Get all relevant information related to a datapoint."""
