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
    series_info: Optional[List[Dict]],
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
        "seriesInfo": series_info,
        "metaData": meta_data,
    }


def dicom_rb_format(task: Dict) -> Dict:
    """Get new dicom rb task format."""
    # pylint: disable=too-many-branches
    if sum(
        map(
            lambda val: len(val.get("itemsIndices", []) or []) if val else 0,
            task.get("seriesInfo", []) or [],
        )
    ) != len(task.get("items", []) or []):
        return {key: value for key, value in task.items() if key not in ("seriesInfo",)}

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

    output["series"] = [{} for _ in range(len(task["seriesInfo"]))]
    for volume_index, series_info in enumerate(task["seriesInfo"]):
        if series_info.get("name"):
            output["series"][volume_index]["name"] = series_info["name"]
        output["series"][volume_index]["items"] = list(
            map(lambda idx: task["items"][idx], series_info["itemsIndices"])  # type: ignore
        )

    for volume_index, label_map in enumerate(task.get("labelsMap", []) or []):
        if label_map.get("labelName"):
            output["series"][volume_index]["segmentations"] = label_map["labelName"]

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
        if label.get("tasklevelclassify"):
            output["classification"] = category
        elif label.get("point3d"):
            volume["landmarks"] = volume.get("landmarks", [])
            volume["landmarks"].append(
                {
                    "x": label["point3d"]["pointx"],
                    "y": label["point3d"]["pointy"],
                    "z": label["point3d"]["pointz"],
                    "category": category,
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
                    "category": category,
                }
            )
        elif label.get("length3d"):
            volume["measurements"] = volume.get("measurements", [])
            volume["measurements"].append(
                {
                    "type": "length",
                    "point1": label["length3d"]["point1"],
                    "point2": label["length3d"]["point2"],
                    "normal": label["length3d"]["normal"],
                    "length": label["length3d"]["computedlength"],
                    "category": category,
                }
            )
        elif label.get("angle3d"):
            volume["measurements"] = volume.get("measurements", [])
            volume["measurements"].append(
                {
                    "type": "angle",
                    "point1": label["angle3d"]["point1"],
                    "point2": label["angle3d"]["point2"],
                    "vertex": label["angle3d"]["point3"],
                    "normal": label["angle3d"]["normal"],
                    "angle": label["angle3d"]["computedangledeg"],
                    "category": category,
                }
            )

    return output
