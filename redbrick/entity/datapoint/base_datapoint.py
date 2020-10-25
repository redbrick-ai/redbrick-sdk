"""
Base class for datapoints.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Union, Dict, Any
import datetime


@dataclass
class BaseDatapoint:
    """Base class representation of a datapoint."""

    org_id: str
    label_set_name: str
    taxonomy: Dict[str, int]
    task_type: str
    remote_labels: List[Any]

    def show_data(self, show_gt: bool = True, ax: Any = None) -> None:
        """Show the data with the ground truth."""
        raise NotImplementedError()
