"""
Base labelset.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class LabelsetBase:
    """Base class for labelset."""

    org_id: str
    labelset_name: str
    task_type: str
    data_type: str
    taxonomy: Dict[str, int]
    dp_ids: List[str] = field(init=False)
    users: Dict[Any, Any]

    def __getitem__(self, index: int) -> Any:
        """Get a single dp."""
        raise NotImplementedError()
