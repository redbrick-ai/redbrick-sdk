"""Utilities for working with label objects."""

from typing import Dict, List, Optional


def clean_rb_label(label: Dict) -> Dict:
    """Clean any None fields."""
    for key, val in label.copy().items():
        if val is None:
            del label[key]
    return label


def flat_rb_format(
    labels: List[Dict],
    items: List[str],
    items_presigned: List[str],
    name: str,
    created_by: str,
    task_id: str,
    current_stage_name: str,
    labels_map: Optional[List[Dict]],
) -> Dict:
    """Get standard rb flat format, same as import format."""
    return {
        "labels": labels,
        "items": items,
        "itemsPresigned": items_presigned,
        "name": name,
        "taskId": task_id,
        "createdBy": created_by,
        "currentStageName": current_stage_name,
        "labelsMap": labels_map or [],
    }
