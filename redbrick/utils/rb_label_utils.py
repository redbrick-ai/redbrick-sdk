"""Utilities for working with label objects."""
import os
from typing import Any, Dict, List, Optional
import json
from copy import deepcopy

from redbrick.stage import ReviewStage


def clean_rb_label(label: Dict) -> Dict:
    """Clean any None fields."""
    for key, val in label.copy().items():
        if val is None:
            del label[key]
    return label


def user_format(user: Optional[str], users: Dict[str, str]) -> Optional[str]:
    """User format."""
    if not user:
        return user
    if user.startswith("RB:"):
        return "System"
    if user.startswith("API:"):
        return "API Key"
    return users.get(user, user)


def assignee_format(
    task: Optional[Dict[str, Any]], users: Dict[str, str]
) -> Optional[Dict]:
    """Assignee format."""
    if not task:
        return None

    user_val = user_format((task.get("assignedTo", {}) or {}).get("userId"), users)
    if not user_val:
        return None

    assignee = {"user": user_val, "status": task["state"]}
    if task.get("assignedAt"):
        assignee["assignedAt"] = task["assignedAt"]
    if task.get("progressSavedAt"):
        assignee["lastSavedAt"] = task["progressSavedAt"]
    if task.get("completedAt"):
        assignee["completedAt"] = task["completedAt"]
    if task.get("completionTimeMs") is not None:
        assignee["timeSpentMs"] = task["completionTimeMs"]

    return assignee


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
    assignee = task.get("assignedTo", {}) or {}
    return {
        "status": task.get("state"),
        "assignee": user_format(
            assignee.get("userId"),
            {
                assignee.get("userId", ""): assignee.get(
                    "email", assignee.get("userId", "")
                )
            },
        ),
        **from_rb_task_data(task.get("taskData", {}) or {}),
    }


def from_rb_consensus_info(task: Dict) -> Dict:
    """Get consensus info from task."""
    scores = []
    for task_score in task.get("scores", []) or []:
        assignee = task_score["user"]
        score: Dict[str, Any] = {
            "assignee": user_format(
                assignee.get("userId"),
                {
                    assignee.get("userId", ""): assignee.get(
                        "email", assignee.get("userId", "")
                    )
                },
            )
        }
        score["score"] = (task_score.get("score", 0) or 0) * 100
        scores.append(score)

    assignee = task.get("user", {}) or {}
    return {
        "assignee": user_format(
            assignee.get("userId"),
            {
                assignee.get("userId", ""): assignee.get(
                    "email", assignee.get("userId", "")
                )
            },
        ),
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
    priority: Optional[float],
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
        "priority": priority,
    }

    if current_stage_sub_task:
        if current_stage_sub_task.get("subTasks"):
            task["consensusTasks"] = [from_rb_sub_task(current_stage_sub_task)]
            for sub_task in current_stage_sub_task["subTasks"]:
                task["consensusTasks"].append(from_rb_sub_task(sub_task))

        elif len(current_stage_sub_task.get("consensusInfo", []) or []) > 1:
            task["consensusScore"] = (
                current_stage_sub_task.get("overallConsensusScore", 0) or 0
            ) * 100

            task["consensusTasks"] = []
            for consensus_task in current_stage_sub_task["consensusInfo"]:
                task["consensusTasks"].append(from_rb_consensus_info(consensus_task))

    return task


def parse_entry_latest(item: Dict) -> Dict:
    """Parse entry latest."""
    try:
        task_id = item["taskId"]
        task_data = item["latestTaskData"]
        datapoint = task_data["dataPoint"]
        items = datapoint["items"]
        items_presigned = datapoint.get("itemsPresigned", []) or []
        name = datapoint["name"]
        created_by = (datapoint.get("createdByEntity", {}) or {}).get("email")
        created_at = datapoint["createdAt"]
        updated_by = task_data["createdByEmail"]
        updated_at = task_data["createdAt"]
        labels = [
            clean_rb_label(label) for label in json.loads(task_data["labelsData"])
        ]
        storage_id = datapoint["storageMethod"]["storageId"]
        label_storage_id = task_data["labelsStorage"]["storageId"]

        return flat_rb_format(
            labels,
            items,
            items_presigned,
            name,
            created_by,
            created_at,
            updated_by,
            updated_at,
            task_id,
            item["currentStageName"],
            item["priority"],
            task_data.get("labelsMap", []) or [],
            datapoint.get("seriesInfo"),
            json.loads(datapoint["metaData"]) if datapoint.get("metaData") else None,
            storage_id,
            label_storage_id,
            item.get("currentStageSubTask"),
        )
    except (AttributeError, KeyError, TypeError, json.decoder.JSONDecodeError):
        return {}


def dicom_rb_series(
    item_index_map: Dict[int, int], input_task: Dict, output_task: Dict, taxonomy: Dict
) -> None:
    """Get standard rb flat format, same as import format."""
    # pylint: disable=too-many-branches, too-many-statements, too-many-locals
    labels = input_task.get("labels", []) or []
    labels_map = input_task.get("labelsMap", []) or []
    series = output_task["series"]

    segmentation_mapping: Dict[int, Dict[Optional[str], str]] = {}
    for idx, label_map in enumerate(labels_map):
        volume_index = (
            item_index_map[label_map["imageIndex"]]
            if "imageIndex" in label_map and label_map["imageIndex"] in item_index_map
            else idx
        )
        segmentation_mapping[volume_index] = {}

        if volume_index >= len(series):
            series.extend([{} for _ in range(volume_index - len(series) + 1)])
        if label_map and label_map.get("labelName"):
            series[volume_index]["segmentations"] = label_map["labelName"]
            series[volume_index]["segmentMap"] = {}
            series[volume_index]["binaryMask"] = (
                label_map.get("binaryMask", False) or False
            )
            series[volume_index]["semanticMask"] = (
                label_map.get("semanticMask", False) or False
            )
            series[volume_index]["pngMask"] = label_map.get("pngMask", False) or False

            if isinstance(series[volume_index]["segmentations"], str):
                segmentation_mapping[volume_index][None] = series[volume_index][
                    "segmentations"
                ]
            elif series[volume_index]["binaryMask"] and isinstance(
                series[volume_index]["segmentations"], list
            ):
                for segmentation in series[volume_index]["segmentations"]:
                    segmentation_mapping[volume_index][
                        os.path.basename(segmentation)
                    ] = segmentation

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
        if isinstance(label.get("frameindex"), int) and label["frameindex"] >= 0:
            video_metadata = {
                "video": {
                    "frameIndex": label["frameindex"],
                    "trackId": label.get("trackid", ""),
                    "keyFrame": label.get("keyframe", True),
                    "endTrack": label.get("end", True),
                }
            }

        items: List[str] = volume.get("items", []) or []

        measurement_stats = {}
        if isinstance(label.get("stats"), dict):
            measurement_stats = {
                "stats": {
                    prop: val for prop, val in label["stats"].items() if val is not None
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
        elif label.get("instanceclassify"):
            volume["instanceClassifications"] = (
                volume.get("instanceClassifications", []) or []
            )
            volume["instanceClassifications"].append(
                {
                    "fileIndex": label["frameindex"],
                    "fileName": items[label["frameindex"]]
                    if label["frameindex"] < len(items)
                    else "",
                    "values": label_obj["attributes"] or {},
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
                series[volume_index]["binaryMask"] = (
                    series[volume_index].get("binaryMask", False) or False
                )
                series[volume_index]["semanticMask"] = (
                    series[volume_index].get("semanticMask", False) or False
                )
                series[volume_index]["pngMask"] = (
                    series[volume_index].get("pngMask", False) or False
                )
                instance: Optional[str] = None
                if bool(taxonomy.get("isNew")) and series[volume_index]["semanticMask"]:
                    instance = (
                        str(label["classid"] + 1)
                        if label["classid"] + 1
                        not in series[volume_index]["segmentMap"]
                        else None
                    )
                else:
                    instance = str(label["dicom"]["instanceid"])
                if instance is not None:
                    mask = (segmentation_mapping.get(volume_index, {}) or {}).get(
                        f"mask-{instance}.png"
                        if series[volume_index]["pngMask"]
                        else f"category-{instance}.nii.gz"
                        if series[volume_index]["semanticMask"]
                        else f"instance-{instance}.nii.gz"
                        if series[volume_index]["binaryMask"]
                        else None
                    )
                    if mask:
                        series[volume_index]["segmentMap"][instance] = {
                            **label_obj,
                            "mask": mask,
                        }
                    else:
                        series[volume_index]["segmentMap"][instance] = {**label_obj}
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
        elif label.get("ellipse"):
            volume["ellipses"] = volume.get("ellipses", [])
            volume["ellipses"].append(
                {
                    "pointCenter": {
                        "xNorm": label["ellipse"]["xcenternorm"],
                        "yNorm": label["ellipse"]["ycenternorm"],
                    },
                    "xRadiusNorm": label["ellipse"]["xnorm"],
                    "yRadiusNorm": label["ellipse"]["ynorm"],
                    "rotationRad": label["ellipse"]["rot"],
                    **label_obj,
                    **video_metadata,
                    **measurement_stats,
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
                    **measurement_stats,
                }
            )
        elif label.get("cuboid"):
            volume["cuboids"] = volume.get("cuboids", [])
            volume["cuboids"].append(
                {
                    "point1": dict(zip("ijk", label["cuboid"]["point1"])),
                    "point2": dict(zip("ijk", label["cuboid"]["point2"])),
                    "absolutePoint1": dict(
                        zip("xyz", label["cuboid"]["computedpoint1world"])
                    ),
                    "absolutePoint2": dict(
                        zip("xyz", label["cuboid"]["computedpoint2world"])
                    ),
                    **label_obj,
                    **measurement_stats,
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
                    **measurement_stats,
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
                    **measurement_stats,  # type: ignore
                }
            )


def dicom_rb_format(
    task: Dict,
    taxonomy: Dict,
    old_format: bool,
    no_consensus: bool,
    review_stages: List[ReviewStage],
) -> Dict:
    """Get new dicom rb task format."""
    # pylint: disable=too-many-branches, too-many-statements, too-many-locals, unused-argument
    if old_format:
        keys = ["itemsPresigned", "seriesInfo", "storageId", "labelStorageId"]
        for key in [
            "currentStageName",
            "priority",
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

    if task.get("priority") is not None:
        output["priority"] = task["priority"]

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
    item_index_map: Dict[int, int] = {}
    for volume_index, series_info in enumerate(task["seriesInfo"]):
        series = volume_series[volume_index]
        if series_info.get("name"):
            series["name"] = series_info["name"]

        series_meta_data = series_info.get("metaData")
        if isinstance(series_meta_data, str):
            series["metaData"] = json.loads(series_meta_data)

        series["items"] = []
        for item_index in series_info["itemsIndices"]:
            item_index_map[item_index] = volume_index
            series["items"].append(task["items"][item_index])

    output["series"] = deepcopy(volume_series)
    if no_consensus:
        if task.get("consensusTasks"):
            consensus_task = task["consensusTasks"][0]
            task["labels"] = consensus_task.get("labels")
            task["labelsMap"] = consensus_task.get("labelsMap")
        dicom_rb_series(item_index_map, task, output, taxonomy)
    else:
        output["consensus"] = True
        if "consensusScore" in task:  # Review_1, END
            output["consensusScore"] = task["consensusScore"]

        if (
            task["currentStageName"] in [stage.stage_name for stage in review_stages]
            and "consensusScore" not in task
        ) or task[
            "currentStageName"
        ] == "END":  # Review_2...n, END
            output["superTruth"] = {}
            if task.get("updatedBy"):
                output["superTruth"]["updatedBy"] = task["updatedBy"]
            if task.get("updatedAt"):
                output["superTruth"]["updatedAt"] = task["updatedAt"]
            output["superTruth"]["series"] = [{**series} for series in volume_series]
            dicom_rb_series(item_index_map, task, output["superTruth"], taxonomy)

        output["consensusTasks"] = [
            {} for _ in range(len(task.get("consensusTasks", []) or []))
        ]
        for consensus_idx, output_consensus_task in enumerate(output["consensusTasks"]):
            consensus_task = task["consensusTasks"][consensus_idx]
            if consensus_task.get("status"):
                output_consensus_task["status"] = consensus_task["status"]

            if consensus_task.get("assignee"):
                output_consensus_task["updatedBy"] = consensus_task["assignee"]
            elif consensus_task.get("email"):
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

                    if consensus_score.get("assignee"):
                        score["secondaryUser"] = consensus_score["assignee"]
                    elif consensus_score.get("email"):
                        score["secondaryUserEmail"] = consensus_score["email"]

                    if consensus_score.get("score") is not None:
                        score["score"] = consensus_score["score"]
                    output_consensus_task["scores"].append(score)

            output_consensus_task["series"] = [{**series} for series in volume_series]

            dicom_rb_series(
                item_index_map, consensus_task, output_consensus_task, taxonomy
            )

    return output
