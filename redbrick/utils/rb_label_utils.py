"""Utilities for working with label objects."""
from typing import Any, Dict, List, Optional
import json


def clean_rb_label(label: Dict) -> Dict:
    """Clean any None fields."""
    for key, val in label.copy().items():
        if val is None:
            del label[key]
    return label


def from_rb_assignee(assignee: Dict) -> Dict:
    """Get assignee object from assignee."""
    return {
        "userId": assignee.get("userId"),
        "email": assignee.get("email"),
    }


def from_rb_task_data(task_data: Dict) -> Dict:
    """Get object from task data."""
    return {
        "updatedAt": task_data.get("createdAt"),
        "labels": [
            clean_rb_label(label)
            for label in json.loads(task_data.get("labelsData", "[]") or "[]")
        ],
        "labelsMap": task_data.get("labelsMap", []) or [],
        "labelStorageId": (task_data.get("labelsStorage", {}) or {}).get("storageId"),
    }


def from_rb_sub_task(task: Dict) -> Dict:
    """Get task object from sub task."""
    return {
        "status": task.get("state"),
        **from_rb_assignee(task.get("assignedTo", {}) or {}),
        **from_rb_task_data(task.get("taskData", {}) or {}),
    }


def from_rb_consensus_info(task: Dict) -> Dict:
    """Get consensus info from task."""
    scores = []
    for task_score in task.get("scores", []) or []:
        score = {**from_rb_assignee(task_score["user"])}
        score["score"] = (task_score.get("score", 0) or 0) * 100
        scores.append(score)

    return {
        **from_rb_assignee(task.get("user", {}) or {}),
        **from_rb_task_data(task.get("taskData", {}) or {}),
        "scores": scores,
    }


def flat_rb_format(
    labels: List[Dict],
    items: List[str],
    items_presigned: List[str],
    name: str,
    created_by: Optional[str],
    created_at: str,
    updated_by: str,
    updated_at: str,
    task_id: str,
    current_stage_name: str,
    labels_map: List[Optional[Dict]],
    series_info: Optional[List[Dict]],
    meta_data: Optional[Dict],
    storage_id: str,
    label_storage_id: str,
    current_stage_sub_task: Optional[Dict],
) -> Dict:
    """Get standard rb flat format, same as import format."""
    # pylint: disable=too-many-locals
    task: Dict[str, Any] = {
        "taskId": task_id,
        "name": name,
        "items": items,
        "itemsPresigned": items_presigned,
        "currentStageName": current_stage_name,
        "createdBy": created_by,
        "createdAt": created_at,
        "updatedBy": updated_by,
        "updatedAt": updated_at,
        "labels": labels,
        "labelsMap": labels_map,
        "seriesInfo": series_info,
        "metaData": meta_data,
        "storageId": storage_id,
        "labelStorageId": label_storage_id,
    }

    if current_stage_sub_task and current_stage_sub_task.get("subTasks"):
        task["consensusTasks"] = [from_rb_sub_task(current_stage_sub_task)]
        for sub_task in current_stage_sub_task["subTasks"]:
            task["consensusTasks"].append(from_rb_sub_task(sub_task))

    elif (
        current_stage_sub_task
        and len(current_stage_sub_task.get("consensusInfo", []) or []) > 1
    ):
        task["consensusScore"] = (
            current_stage_sub_task.get("overallConsensusScore", 0) or 0
        ) * 100

        task["consensusTasks"] = []
        for consensus_task in current_stage_sub_task["consensusInfo"]:
            task["consensusTasks"].append(from_rb_consensus_info(consensus_task))

    return task


def dicom_rb_series(input_task: Dict, output_task: Dict) -> None:
    """Get standard rb flat format, same as import format."""
    # pylint: disable=too-many-branches, too-many-statements
    labels = input_task.get("labels", []) or []
    labels_map = input_task.get("labelsMap", []) or []
    series = output_task["series"]
    for volume_index, label_map in enumerate(labels_map):
        if volume_index >= len(series):
            series.extend([{} for _ in range(volume_index - len(series) + 1)])
        if label_map and label_map.get("labelName"):
            series[volume_index]["segmentations"] = label_map["labelName"]
            series[volume_index]["segmentMap"] = {}

    for label in labels:
        volume_index = label.get("volumeindex", 0)
        if volume_index >= len(series):
            series.extend([{} for _ in range(volume_index - len(series) + 1)])

    for label in labels:
        volume = series[label.get("volumeindex", 0)]
        label_obj = {}
        if "category" in label and label["category"] is not None:
            label_obj["category"] = (
                label["category"]
                if not isinstance(label["category"], list)
                else label["category"][0][1]
                if isinstance(label["category"][0], list)
                and len(label["category"][0]) == 2
                else label["category"][0][1:]
                if isinstance(label["category"][0], list)
                and len(label["category"][0]) > 2
                else label["category"]
            )

        attributes = {}
        for attribute in label.get("attributes", []) or []:
            attributes[attribute["name"]] = (
                attribute["value"]
                if not isinstance(attribute["value"], str)
                else True
                if attribute["value"].lower() == "true"
                else False
                if attribute["value"].lower() == "false"
                else attribute["value"]
            )
        if attributes:
            label_obj["attributes"] = attributes

        video_metadata = {}
        if (
            len(volume.get("items", []) or []) > 1
            and isinstance(label.get("frameindex"), int)
            and label["frameindex"] >= 0
        ):
            video_metadata = {
                "video": {
                    "frameIndex": label["frameindex"],
                    "trackId": label.get("trackid", ""),
                    "keyFrame": label.get("keyframe", True),
                    "endTrack": label.get("end", True),
                }
            }

        if label.get("tasklevelclassify") or label.get("studyclassify"):
            output_task["classification"] = {**label_obj}
        elif label.get("multiclassify") or label.get("seriesclassify"):
            volume["classifications"] = volume.get("classifications", []) or []
            volume["classifications"].append(
                {
                    **label_obj,
                    **video_metadata,
                }
            )
        elif label.get("dicom", {}).get("instanceid"):
            volume_indices = (
                [label["volumeindex"]]
                if isinstance(label.get("volumeindex"), int)
                and 0 <= label["volumeindex"] < len(series)
                else list(range(len(series)))
            )
            for volume_index in volume_indices:
                series[volume_index]["segmentMap"] = series[volume_index].get(
                    "segmentMap", {}
                )
                series[volume_index]["segmentMap"][
                    str(label["dicom"]["instanceid"])
                ] = {**label_obj}
        elif label.get("length3d"):
            volume["measurements"] = volume.get("measurements", [])
            volume["measurements"].append(
                {
                    "type": "length",
                    "point1": dict(zip("ijk", label["length3d"]["point1"])),
                    "point2": dict(zip("ijk", label["length3d"]["point2"])),
                    "absolutePoint1": dict(
                        zip("xyz", label["length3d"]["computedpoint1world"])
                    ),
                    "absolutePoint2": dict(
                        zip("xyz", label["length3d"]["computedpoint2world"])
                    ),
                    "normal": label["length3d"]["normal"],
                    "length": label["length3d"]["computedlength"],
                    **label_obj,
                }
            )
        elif label.get("angle3d"):
            volume["measurements"] = volume.get("measurements", [])
            volume["measurements"].append(
                {
                    "type": "angle",
                    "point1": dict(zip("ijk", label["angle3d"]["point1"])),
                    "vertex": dict(zip("ijk", label["angle3d"]["point2"])),
                    "point2": dict(zip("ijk", label["angle3d"]["point3"])),
                    "absolutePoint1": dict(
                        zip("xyz", label["angle3d"]["computedpoint1world"])
                    ),
                    "absoluteVertex": dict(
                        zip("xyz", label["angle3d"]["computedpoint2world"])
                    ),
                    "absolutePoint2": dict(
                        zip("xyz", label["angle3d"]["computedpoint3world"])
                    ),
                    "normal": label["angle3d"]["normal"],
                    "angle": label["angle3d"]["computedangledeg"],
                    **label_obj,
                }
            )
        elif label.get("point"):
            volume["landmarks"] = volume.get("landmarks", [])
            volume["landmarks"].append(
                {
                    "point": {
                        "xNorm": label["point"]["xnorm"],
                        "yNorm": label["point"]["ynorm"],
                    },
                    **label_obj,
                    **video_metadata,
                }
            )
        elif label.get("point3d"):
            volume["landmarks3d"] = volume.get("landmarks3d", [])
            volume["landmarks3d"].append(
                {
                    "point": {
                        "i": label["point3d"]["pointx"],
                        "j": label["point3d"]["pointy"],
                        "k": label["point3d"]["pointz"],
                    },
                    **label_obj,
                }
            )
        elif label.get("polyline"):
            volume["polylines"] = volume.get("polylines", [])
            volume["polylines"].append(
                {
                    "points": [
                        {"xNorm": point["xnorm"], "yNorm": point["ynorm"]}
                        for point in label["polyline"]
                    ],
                    **label_obj,  # type: ignore
                    **video_metadata,  # type: ignore
                }
            )
        elif label.get("bbox2d"):
            volume["boundingBoxes"] = volume.get("boundingBoxes", [])
            volume["boundingBoxes"].append(
                {
                    "pointTopLeft": {
                        "xNorm": label["bbox2d"]["xnorm"],
                        "yNorm": label["bbox2d"]["ynorm"],
                    },
                    "wNorm": label["bbox2d"]["wnorm"],
                    "hNorm": label["bbox2d"]["hnorm"],
                    **label_obj,
                    **video_metadata,
                }
            )
        elif label.get("bbox3d"):
            volume["boundingBoxes3d"] = volume.get("boundingBoxes3d", [])
            volume["boundingBoxes3d"].append(
                {
                    "pointTopLeft": {
                        "i": label["bbox3d"]["pointx"],
                        "j": label["bbox3d"]["pointy"],
                        "k": label["bbox3d"]["pointz"],
                    },
                    "width": label["bbox3d"]["deltax"],
                    "height": label["bbox3d"]["deltay"],
                    "depth": label["bbox3d"]["deltaz"],
                    **label_obj,
                    **video_metadata,
                }
            )
        elif label.get("polygon"):
            volume["polygons"] = volume.get("polygons", [])
            volume["polygons"].append(
                {
                    "points": [
                        {"xNorm": point["xnorm"], "yNorm": point["ynorm"]}
                        for point in label["polygon"]
                    ],
                    **label_obj,  # type: ignore
                    **video_metadata,  # type: ignore
                }
            )


def dicom_rb_format(task: Dict, old_format: bool, no_consensus: bool) -> Dict:
    """Get new dicom rb task format."""
    # pylint: disable=too-many-branches, too-many-statements, too-many-locals
    if old_format:
        keys = ["itemsPresigned", "seriesInfo", "storageId", "labelStorageId"]
        for key in [
            "currentStageName",
            "createdBy",
            "createdAt",
            "updatedBy",
            "updatedAt",
            "labels",
            "labelsMap",
            "metaData",
        ]:
            if not task.get(key):
                keys.append(key)
        return {key: value for key, value in task.items() if key not in keys}

    if not task.get("seriesInfo"):
        task["seriesInfo"] = [{"itemsIndices": list(range(len(task["items"])))}]

    output = {"taskId": task["taskId"]}

    if task.get("name"):
        output["name"] = task["name"]
    elif task.get("items"):
        output["name"] = task["items"][0]

    if task.get("currentStageName"):
        output["currentStageName"] = task["currentStageName"]

    if task.get("createdBy"):
        output["createdBy"] = task["createdBy"]

    if task.get("createdAt"):
        output["createdAt"] = task["createdAt"]

    if task.get("updatedBy"):
        output["updatedBy"] = task["updatedBy"]

    if task.get("updatedAt"):
        output["updatedAt"] = task["updatedAt"]

    if task.get("metaData"):
        output["metaData"] = task["metaData"]

    volume_series: List[Dict] = [{} for _ in range(len(task["seriesInfo"]))]
    for volume_index, series_info in enumerate(task["seriesInfo"]):
        series = volume_series[volume_index]
        if series_info.get("name"):
            series["name"] = series_info["name"]
        if series_info.get("numFrames"):
            series["numFrames"] = series_info["numFrames"]
        if series_info.get("dimensions"):
            series["dimensions"] = series_info["dimensions"]
        series["items"] = list(
            map(lambda idx: task["items"][idx], series_info["itemsIndices"])  # type: ignore
        )

    if no_consensus:
        if task.get("consensusTasks"):
            consensus_task = task["consensusTasks"][0]
            task["labels"] = consensus_task.get("labels")
            task["labelsMap"] = consensus_task.get("labelsMap")
        output["series"] = volume_series
        dicom_rb_series(task, output)
    else:
        if not task.get("consensusTasks"):
            task["consensusTasks"] = [
                {
                    "email": task.get("updatedBy"),
                    "updatedAt": task.get("updatedAt"),
                    "labels": task.get("labels"),
                    "labelsMap": task.get("labelsMap"),
                }
            ]

        output["consensus"] = True
        if "consensusScore" in task:
            output["consensusScore"] = task["consensusScore"]
        output["consensusTasks"] = [{} for _ in range(len(task["consensusTasks"]))]
        for consensus_idx, output_consensus_task in enumerate(output["consensusTasks"]):
            consensus_task = task["consensusTasks"][consensus_idx]
            if consensus_task.get("status"):
                output_consensus_task["status"] = consensus_task["status"]
            if consensus_task.get("email"):
                output_consensus_task["updatedBy"] = consensus_task["email"]
            if consensus_task.get("userId"):
                output_consensus_task["updatedByUserId"] = consensus_task["userId"]
            if consensus_task.get("updatedAt"):
                output_consensus_task["updatedAt"] = consensus_task["updatedAt"]

            if consensus_task.get("scores"):
                output_consensus_task["scores"] = []
                for consensus_score in consensus_task["scores"] or []:
                    score = {}
                    if consensus_score.get("userId"):
                        score["secondaryUserId"] = consensus_score["userId"]
                    if consensus_score.get("email"):
                        score["secondaryUserEmail"] = consensus_score["email"]
                    if consensus_score.get("score"):
                        score["score"] = consensus_score["score"]
                    output_consensus_task["scores"].append(score)

            output_consensus_task["series"] = [{**series} for series in volume_series]

            dicom_rb_series(consensus_task, output_consensus_task)

    return output
