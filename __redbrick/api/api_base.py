"""Abstract interface to RedBrick API."""

from typing import List, Union, Dict, Any
from abc import ABC, abstractmethod
from redbrick.entity.datapoint import Image, Video


class RedBrickApiBase(ABC):
    """Abstract interface to RedBrick API."""

    @abstractmethod
    def get_datapoint_ids(self, org_id: str, label_set_name: str) -> List[str]:
        """Get a list of datapoint ids in labelset."""

    @abstractmethod
    def get_datapoint(
        self,
        org_id: str,
        label_set_name: str,
        dp_id: str,
        task_type: str,
        taxonomy: Dict[Any, Any],
    ) -> Union[Image, Video]:
        """Get all relevant information related to a datapoint."""
