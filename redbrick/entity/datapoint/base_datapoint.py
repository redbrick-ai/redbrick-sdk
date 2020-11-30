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
    created_by: str
    remote_labels: List[Any]
