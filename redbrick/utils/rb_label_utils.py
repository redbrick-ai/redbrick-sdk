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


def dicom_rb_format(task: Dict) -> Dict:
    """Get new dicom rb task format."""
    # pylint: disable=too-many-branches
    output = {"taskId": task["taskId"]}

    if task.get("name"):
        output["name"] = task["name"]
    elif task.get("items"):
        output["name"] = task["items"][0]

    if task.get("createdBy"):
        output["createdBy"] = task["createdBy"]

    if task.get("currentStageName"):
        output["currentStageName"] = task["currentStageName"]

    if task.get("items"):
        output["items"] = task["items"]

    if task.get("itemsPresigned"):
        output["itemsPresigned"] = task["itemsPresigned"]

    if task.get("labelsMap"):
        input_labels_map = task["labelsMap"]
        segmentations = {
            str(label_map["imageIndex"]): label_map["labelName"]
            for label_map in input_labels_map
            if label_map["labelName"]
        }
        keys = list(map(int, segmentations.keys()))

        if sorted(keys) == list(range(len(input_labels_map))):
            output["segmentations"] = [None for _ in keys]
            for label_map in input_labels_map:
                output["segmentations"][label_map["imageIndex"]] = label_map[
                    "labelName"
                ]
        elif keys:
            output["segmentations"] = segmentations

    if task.get("labels"):
        input_labels = task["labels"]
        segment_map = {}
        labels = []
        for label in input_labels:
            if label.get("dicom", {}).get("instanceid"):
                segment_map[str(label["dicom"]["instanceid"])] = (
                    label["category"][0][1]
                    if len(label["category"][0]) == 2
                    else label["category"][0][1:]
                )
            else:
                labels.append(clean_rb_label(label))

        if segment_map:
            output["segmentMap"] = segment_map

        if labels:
            output["labels"] = labels

    return output
