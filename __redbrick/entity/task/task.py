"""
Class representation of a task.
"""
from dataclasses import dataclass
from typing import Dict, Any
from redbrick.utils import url_to_image
import numpy as np  # type: ignore


@dataclass
class Task:
    """Class representation of a task."""

    org_id: str
    project_id: str
    stage_name: str
    task_id: str
    dp_id: str
    sub_name: str
    taxonomy: Dict[Any, Any]
    items_list: str
    items_list_presigned: str
    task_data_type: str

    @staticmethod
    def get_data(presigned_url: str) -> np.ndarray:
        """Get the frame/image data."""
        return url_to_image(presigned_url)
