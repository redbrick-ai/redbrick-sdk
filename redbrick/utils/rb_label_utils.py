"""Utilities for working with label objects."""

from typing import Dict, List


def clean_rb_label(label: Dict) -> Dict:
    """Clean any None fields."""
    for k, v in label.copy().items():
        if v is None:
            del label[k]
    return label


def flat_rb_format(
    labels: List[Dict],
    items: List[str],
    items_presigned: List[str],
    name: str,
    dp_id: str,
    created_by: str,
    task_id: str,
) -> Dict:
    """Get standard rb flat format, same as import format."""
    return {
        "labels": labels,
        "items": items,
        "itemsPresigned": items_presigned,
        "name": name,
        "dpId": dp_id,
        "taskId": task_id,
        "createdBy": created_by,
    }
