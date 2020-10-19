"""
Class representation of a task.
"""
from dataclasses import dataclass


@dataclass
class Task:
    """Class representation of a task."""

    org_id: str
    project_id: str
    stage_name: str
    task_id: str
    dp_id: str
    sub_name: str
    taxonomy: dict
    items_list: str
    items_list_presigned: str
    task_data_type: str
