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
    labels_map: List[Dict],
    items_indices: Optional[Dict[str, List[int]]],
    meta_data: Optional[Dict],
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
        "labelsMap": labels_map,
        "itemsIndices": items_indices,
        "metaData": meta_data,
    }


def dicom_rb_format(task: Dict) -> Dict:
    """Get new dicom rb task format."""
    # pylint: disable=too-many-branches
    if not task.get("itemsIndices"):
        return task

    output = {"taskId": task["taskId"]}

    if task.get("name"):
        output["name"] = task["name"]
    elif task.get("items"):
        output["name"] = task["items"][0]

    if task.get("createdBy"):
        output["createdBy"] = task["createdBy"]

    if task.get("currentStageName"):
        output["currentStageName"] = task["currentStageName"]

    if task.get("metaData"):
        output["metaData"] = task["metaData"]

    output["series"] = [{} for _ in range(len(task["itemsIndices"]))]
    for volume_index, indices in task["itemsIndices"].items():
        output["series"][int(volume_index)]["items"] = list(
            map(lambda idx: task["items"][idx], indices)  # type: ignore
        )

    for label_map in task.get("labelsMap", []) or []:
        if label_map.get("labelName"):
            output["series"][label_map["imageIndex"]]["segmentations"] = label_map[
                "labelName"
            ]

    for label in task.get("labels", []) or []:
        category = (
            label["category"][0][1]
            if len(label["category"][0]) == 2
            else label["category"][0][1:]
        )
        if label.get("dicom", {}).get("instanceid"):
            output["segmentMap"] = output.get("segmentMap", {})
            output["segmentMap"][str(label["dicom"]["instanceid"])] = category
            continue

        volume = output["series"][label.get("volumeindex", 0)]
        if label.get("point3d"):
            volume["landmarks"] = volume.get("landmarks", [])
            volume["landmarks"].append(
                {
                    "x": label["point3d"]["pointx"],
                    "y": label["point3d"]["pointy"],
                    "z": label["point3d"]["pointz"],
                    "classification": category,
                }
            )
        elif label.get("bbox3d"):
            volume["boundingBox"] = volume.get("boundingBox", [])
            volume["boundingBox"].append(
                {
                    "x": label["bbox3d"]["pointx"],
                    "y": label["bbox3d"]["pointy"],
                    "z": label["bbox3d"]["pointz"],
                    "width": label["bbox3d"]["deltax"],
                    "height": label["bbox3d"]["deltay"],
                    "depth": label["bbox3d"]["deltaz"],
                    "classification": category,
                }
            )

    return output
