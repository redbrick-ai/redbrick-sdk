"""
Base dataset.
"""
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class DatasetBase:
    """Base class for dataset."""

    org_id: str
    data_set_name: str
    data_type: str
    datapoint_count: int
    desc: str
    createdAt: str
    createdBy: str
    status: str
