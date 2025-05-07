"""Utilities for working with label objects."""

import os
from typing import Any, Dict, List, Optional, Sequence, Union
import json
from copy import deepcopy

from redbrick.common.storage import StorageMethod
from redbrick.stage import ReviewStage
from redbrick.types import task as TaskType
from redbrick.types.taxonomy import Taxonomy
from redbrick.utils.logging import logger


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


def get_world_point(point: List[float]) -> TaskType.WorldPoint:
    """Get the WorldPoint from a point."""
    return {
        "x": point[0],
        "y": point[1],
        "z": point[2],
    }


def get_voxel_point(point: List[int]) -> TaskType.VoxelPoint:
    """Get the VoxelPoint from a point."""
    return {
        "i": point[0],
        "j": point[1],
        "k": point[2],
    }


def from_rb_task_data(task_data: Dict) -> Dict:
    """Get object from task data."""
    if task_data.get("labelsDataPath"):
        labels = None
        labels_data_path = task_data["labelsDataPath"]
    else:
        labels = [
            clean_rb_label(label)
            for label in json.loads(task_data.get("labelsData") or "[]")
        ]
        labels_data_path = None
    return {
        "updatedAt": task_data.get("createdAt"),
        "labels": labels,
        "labelsDataPath": labels_data_path,
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


def convert_datapoint_classifications(
    classifications: List[Dict],
) -> TaskType.Classification:
    """Convert datapoint classifications."""
    attributes: Dict[str, Union[str, bool, List[str]]] = {}
    for attribute in classifications:
        attributes[attribute["name"]] = (
            attribute["value"]
            if not isinstance(attribute["value"], str)
            else (
                True
                if attribute["value"].lower() == "true"
                else (
                    False
                    if attribute["value"].lower() == "false"
                    else attribute["value"]
                )
            )
        )
    return {"attributes": attributes}


def flat_rb_format(
    labels: Optional[List[Dict]],
    labels_data_path: Optional[str],
    items: List[str],
    items_presigned: List[str],
    name: str,
    created_by: Optional[str],
    created_at: str,
    updated_by: Optional[str],
    updated_at: Optional[str],
    task_id: str,
    current_stage_name: str,
    priority: Optional[float],
    labels_map: Sequence[Optional[Dict]],
    series_info: Optional[List[Dict]],
    meta_data: Optional[Dict],
    storage_id: str,
    label_storage_id: Optional[str],
    current_stage_sub_task: Optional[Dict],
    heat_maps: Optional[List[Dict]],
    transforms: Optional[List[Dict]],
    centerlines: Optional[List[Dict]],
    datapoint_classification: Optional[List[Dict]],
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
        "labelsDataPath": labels_data_path,
        "labelsMap": labels_map,
        "seriesInfo": series_info,
        "metaData": meta_data,
        "storageId": storage_id,
        "labelStorageId": label_storage_id,
        "priority": priority,
        "heatMaps": heat_maps,
        "transforms": transforms,
        "centerline": centerlines,
        "datapointClassification": datapoint_classification,
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

        else:
            task["status"] = current_stage_sub_task.get("state")

    return task


def clean_heatmap(heatmap_data: Dict) -> TaskType.HeatMap:
    """Clean heatmap."""
    heatmap: TaskType.HeatMap = {
        "name": heatmap_data["name"],
        "item": heatmap_data["item"],
    }

    if heatmap_data.get("preset"):
        heatmap["preset"] = heatmap_data["preset"]
    if heatmap_data.get("dataRange"):
        heatmap["dataRange"] = heatmap_data["dataRange"]
    if heatmap_data.get("opacityPoints"):
        heatmap["opacityPoints"] = heatmap_data["opacityPoints"]
    if heatmap_data.get("opacityPoints3d"):
        heatmap["opacityPoints3d"] = heatmap_data["opacityPoints3d"]
    if heatmap_data.get("rgbPoints"):
        heatmap["rgbPoints"] = heatmap_data["rgbPoints"]

    return heatmap


def clean_transform(transform_data: Dict) -> TaskType.Transform:
    """Clean transform."""
    return {
        "transform": [
            transform_data["transform"][i : i + 4]
            for i in range(0, len(transform_data["transform"]), 4)
        ]
    }


def clean_centerline(centerline_data: Dict) -> TaskType.Centerline:
    """Clean centerline."""
    return {
        "name": centerline_data["name"],
        "centerline": json.loads(centerline_data["centerline"]),
    }


def parse_entry_latest(item: Dict) -> Dict:
    """Parse entry latest."""
    # pylint: disable=too-many-locals
    try:
        task_id = item["taskId"]
        task_data = item["latestTaskData"] or {}
        datapoint = item["datapoint"]
        items = datapoint["items"]
        items_presigned = datapoint.get("itemsPresigned", []) or []
        name = datapoint["name"]
        created_by = (datapoint.get("createdByEntity", {}) or {}).get("email")
        created_at = datapoint["createdAt"]
        updated_by = task_data.get("createdByEmail")
        updated_at = task_data.get("createdAt")

        if task_data.get("labelsDataPath"):
            labels = None
            labels_data_path = task_data["labelsDataPath"]
        else:
            labels = [
                clean_rb_label(label)
                for label in json.loads(task_data.get("labelsData") or "[]")
            ]
            labels_data_path = None

        storage_id = datapoint["storageMethod"]["storageId"]
        label_storage_id = (task_data.get("labelsStorage") or {}).get(
            "storageId"
        ) or StorageMethod.REDBRICK
        heatmaps = datapoint.get("heatMaps")
        transforms = datapoint.get("transforms")
        centerlines = datapoint.get("centerline")
        if datapoint.get("attributes"):
            datapoint_attributes = json.loads(datapoint["attributes"])
        else:
            datapoint_attributes = None

        return flat_rb_format(
            labels,
            labels_data_path,
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
            heatmaps,
            transforms,
            centerlines,
            datapoint_attributes,
        )
    except (AttributeError, KeyError, TypeError, json.decoder.JSONDecodeError):
        return {}


def dicom_rb_series(
    item_index_map: Dict[int, int],
    input_task: Dict,
    output_task: TaskType.OutputTask,
    taxonomy: Taxonomy,
    without_masks: bool = False,
) -> None:
    """Get standard rb flat format, same as import format."""
    # pylint: disable=too-many-branches, too-many-statements, too-many-locals
    labels: List[Dict] = input_task.get("labels", []) or []
    labels_map: Sequence[Optional[Dict]] = input_task.get("labelsMap", []) or []
    series = output_task["series"]

    segmentation_mapping: Dict[int, Dict[Optional[str], Union[str, List[str]]]] = {}
    for idx, label_map in enumerate(labels_map):
        volume_index: int = (
            label_map["seriesIndex"]
            if label_map and label_map.get("seriesIndex") is not None
            else (
                item_index_map[label_map["imageIndex"]]
                if label_map
                and "imageIndex" in label_map
                and label_map["imageIndex"] in item_index_map
                else idx
            )
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

            segmentations = series[volume_index].get("segmentations")
            if isinstance(segmentations, str):
                segmentation_mapping[volume_index][None] = segmentations
            elif series[volume_index].get("binaryMask") and isinstance(
                segmentations, list
            ):
                for segmentation in segmentations:
                    segmentation_mapping[volume_index][
                        os.path.basename(segmentation)
                    ] = segmentation

    for label in labels:
        volume_index = label.get("volumeindex", 0)
        if volume_index >= len(series):
            series.extend([{} for _ in range(volume_index - len(series) + 1)])

        volume: TaskType.Series = series[volume_index]
        label_obj: TaskType.CommonLabelProps = {}
        if "category" in label and label["category"] is not None:
            label_obj["category"] = (
                label["category"]
                if not isinstance(label["category"], list)
                else (
                    label["category"][0][1]
                    if isinstance(label["category"][0], list)
                    and len(label["category"][0]) == 2
                    else (
                        label["category"][0][1:]
                        if isinstance(label["category"][0], list)
                        and len(label["category"][0]) > 2
                        else label["category"]
                    )
                )
            )

        attributes = {}
        for attribute in label.get("attributes", []) or []:
            attributes[attribute["name"]] = (
                attribute["value"]
                if not isinstance(attribute["value"], str)
                else (
                    True
                    if attribute["value"].lower() == "true"
                    else (
                        False
                        if attribute["value"].lower() == "false"
                        else attribute["value"]
                    )
                )
            )
        if attributes:
            label_obj["attributes"] = attributes

        if label.get("linkid") is not None:
            label_obj["group"] = label["linkid"]
        if label.get("readonly"):
            label_obj["readOnly"] = label["readonly"]

        video_metadata: Dict[str, TaskType.VideoMetaData] = {}
        if (
            isinstance(label.get("globalitemsindex"), int)
            and label["globalitemsindex"] >= 0
        ) or (isinstance(label.get("frameindex"), int) and label["frameindex"] >= 0):
            video_metadata = {
                "video": {
                    "trackId": label.get("trackid", ""),
                    "keyFrame": label.get("keyframe", True),
                    "endTrack": label.get("end", True),
                }
            }
            if (
                # pylint: disable=too-many-boolean-expressions
                isinstance(label.get("globalitemsindex"), int)
                and label["globalitemsindex"] >= 0
                and isinstance(input_task.get("seriesInfo"), list)
                and len(input_task["seriesInfo"]) > volume_index
                and isinstance(input_task["seriesInfo"][volume_index], dict)
                and isinstance(
                    input_task["seriesInfo"][volume_index].get("itemsIndices"),
                    list,
                )
                and label["globalitemsindex"]
                in input_task["seriesInfo"][volume_index]["itemsIndices"]
            ):
                video_metadata["video"]["seriesItemIndex"] = input_task["seriesInfo"][
                    volume_index
                ]["itemsIndices"].index(label["globalitemsindex"])
            if label.get("seriesframeindex") is not None:
                video_metadata["video"]["seriesFrameIndex"] = label["seriesframeindex"]
            if label.get("frameindex") is not None:
                video_metadata["video"]["frameIndex"] = label["frameindex"]

        items: List[str] = volume.get("items", []) or []  # type: ignore

        measurement_stats = {}
        if isinstance(label.get("stats"), dict):
            measurement_stats = {
                "stats": {
                    prop: val for prop, val in label["stats"].items() if val is not None
                }
            }

        if label.get("tasklevelclassify") or label.get("studyclassify"):
            output_task["classification"] = {**label_obj}  # type: ignore
        elif label.get("multiclassify") or label.get("seriesclassify"):
            volume["classifications"] = volume.get("classifications", []) or []
            volume["classifications"].append(
                {
                    **label_obj,  # type: ignore
                    **video_metadata,  # type: ignore
                }
            )
        elif label.get("instanceclassify"):
            volume["instanceClassifications"] = (
                volume.get("instanceClassifications", []) or []
            )
            volume["instanceClassifications"].append(
                {
                    "fileIndex": label["frameindex"],
                    "fileName": (
                        items[label["frameindex"]]
                        if label["frameindex"] < len(items)
                        else ""
                    ),
                    "values": label_obj.get("attributes", {}),
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
                if bool(taxonomy.get("isNew")) and series[volume_index].get(
                    "semanticMask"
                ):
                    instance = (
                        str(label["classid"] + 1)
                        if label["classid"] + 1
                        not in series[volume_index].get("segmentMap", {})
                        else None
                    )
                else:
                    instance = str(label["dicom"]["instanceid"])
                if instance is not None:
                    mask = (segmentation_mapping.get(volume_index, {}) or {}).get(
                        f"mask-{instance}.png"
                        if series[volume_index].get("pngMask")
                        else (
                            f"category-{instance}.nii.gz"
                            if series[volume_index].get("semanticMask")
                            else (
                                f"instance-{instance}.nii.gz"
                                if series[volume_index].get("binaryMask")
                                else None
                            )
                        )
                    )
                    segment_map_instance: TaskType.CommonLabelProps = {**label_obj}
                    if mask:
                        segment_map_instance["mask"] = mask
                    if without_masks and label["dicom"].get("groupids"):
                        segment_map_instance["overlappingGroups"] = label["dicom"][
                            "groupids"
                        ]

                    cur_series = series[volume_index]
                    if "segmentMap" not in cur_series:
                        cur_series["segmentMap"] = {}
                    cur_series["segmentMap"][instance] = segment_map_instance

        elif label.get("length3d"):
            volume["measurements"] = volume.get("measurements", [])
            measurement_length: TaskType.MeasureLength = {
                "type": "length",
                "point1": get_voxel_point(label["length3d"]["point1"]),
                "point2": get_voxel_point(label["length3d"]["point2"]),
                "normal": label["length3d"]["normal"],
                **label_obj,  # type: ignore
            }
            if label["length3d"].get("computedpoint1world"):
                measurement_length["absolutePoint1"] = get_world_point(
                    label["length3d"]["computedpoint1world"]
                )
            if label["length3d"].get("computedpoint2world"):
                measurement_length["absolutePoint2"] = get_world_point(
                    label["length3d"]["computedpoint2world"]
                )
            if label["length3d"].get("computedlength"):
                measurement_length["length"] = label["length3d"]["computedlength"]
            volume["measurements"].append(measurement_length)
        elif label.get("angle3d"):
            volume["measurements"] = volume.get("measurements", [])
            measurement_angle: TaskType.MeasureAngle = {
                "type": "angle",
                "point1": get_voxel_point(label["angle3d"]["point1"]),
                "vertex": get_voxel_point(label["angle3d"]["point2"]),
                "point2": get_voxel_point(label["angle3d"]["point3"]),
                "normal": label["angle3d"]["normal"],
                **label_obj,  # type: ignore
            }
            if label["angle3d"].get("computedpoint1world"):
                measurement_angle["absolutePoint1"] = get_world_point(
                    label["angle3d"]["computedpoint1world"]
                )
            if label["angle3d"].get("computedpoint2world"):
                measurement_angle["absoluteVertex"] = get_world_point(
                    label["angle3d"]["computedpoint2world"]
                )
            if label["angle3d"].get("computedpoint3world"):
                measurement_angle["absolutePoint2"] = get_world_point(
                    label["angle3d"]["computedpoint3world"]
                )
            if label["angle3d"].get("computedangledeg"):
                measurement_angle["angle"] = label["angle3d"]["computedangledeg"]
            volume["measurements"].append(measurement_angle)
        elif label.get("point"):
            volume["landmarks"] = volume.get("landmarks", [])
            volume["landmarks"].append(
                {
                    "point": {
                        "xNorm": label["point"]["xnorm"],
                        "yNorm": label["point"]["ynorm"],
                    },
                    **label_obj,  # type: ignore
                    **video_metadata,  # type: ignore
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
                    **label_obj,  # type: ignore
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
                    **label_obj,  # type: ignore
                    **video_metadata,  # type: ignore
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
                    **label_obj,  # type: ignore
                    **video_metadata,  # type: ignore
                    **measurement_stats,
                }
            )
        elif label.get("cuboid"):
            volume["cuboids"] = volume.get("cuboids", [])
            cuboid: TaskType.Cuboid = {
                "point1": get_voxel_point(label["cuboid"]["point1"]),
                "point2": get_voxel_point(label["cuboid"]["point2"]),
                **label_obj,  # type: ignore
                **measurement_stats,  # type: ignore
            }
            if label["cuboid"].get("computedpoint1world"):
                cuboid["absolutePoint1"] = get_world_point(
                    label["cuboid"]["computedpoint1world"]
                )
            if label["cuboid"].get("computedpoint2world"):
                cuboid["absolutePoint2"] = get_world_point(
                    label["cuboid"]["computedpoint2world"]
                )
            volume["cuboids"].append(cuboid)
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
    taxonomy: Taxonomy,
    old_format: bool,
    no_consensus: bool,
    review_stages: List[ReviewStage],
    without_masks: bool = False,
) -> TaskType.OutputTask:
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
        return {key: value for key, value in task.items() if key not in keys}  # type: ignore

    if not task.get("seriesInfo"):
        task["seriesInfo"] = [{}]
    if any(not series.get("itemsIndices") for series in task["seriesInfo"]):
        task["seriesInfo"][0]["itemsIndices"] = list(range(len(task["items"])))
        if len(task["seriesInfo"]) > 1:
            logger.warning(
                f"{task['taskId']} - Putting all items in first series since split is unknown"
            )
            for series in task["seriesInfo"][1:]:
                series["itemsIndices"] = []

    output: TaskType.OutputTask = {"taskId": task["taskId"], "name": "", "series": []}

    if task.get("name"):
        output["name"] = task["name"]
    elif task.get("items"):
        output["name"] = task["items"][0]

    if task.get("currentStageName"):
        output["currentStageName"] = task["currentStageName"]

    if task.get("status"):
        output["status"] = task["status"]

    if task.get("priority") is not None:
        output["priority"] = task["priority"]

    if task.get("createdBy"):
        output["createdBy"] = task["createdBy"]

    if task.get("createdAt"):
        output["createdAt"] = task["createdAt"]

    if task.get("storageId"):
        output["storageId"] = task["storageId"]

    if task.get("updatedBy"):
        output["updatedBy"] = task["updatedBy"]

    if task.get("updatedAt"):
        output["updatedAt"] = task["updatedAt"]

    if task.get("metaData"):
        output["metaData"] = (
            json.loads(task["metaData"])
            if isinstance(task["metaData"], str)
            else task["metaData"]
        )

    # Task datapoint classification
    if task.get("datapointClassification"):
        output["datapointClassification"] = convert_datapoint_classifications(
            task["datapointClassification"]
        )

    volume_series: List[TaskType.Series] = [{} for _ in range(len(task["seriesInfo"]))]
    item_index_map: Dict[int, int] = {}
    heat_maps: List[Dict] = task.get("heatMaps") or []
    transforms: List[Dict] = task.get("transforms") or []
    centerlines: List[Dict] = task.get("centerline") or []

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

        for heat_map in heat_maps:
            if heat_map.get("seriesIndex") == volume_index:
                series["heatMaps"] = series.get("heatMaps", [])
                series["heatMaps"].append(clean_heatmap(heat_map))

        for tranform in transforms:
            if tranform.get("seriesIndex") == volume_index:
                series["transforms"] = series.get("transforms", [])
                series["transforms"].append(clean_transform(tranform))

        for centerline in centerlines:
            if centerline.get("seriesIndex") == volume_index:
                series["centerline"] = series.get("centerline", [])
                series["centerline"].append(clean_centerline(centerline))

    output["series"] = deepcopy(volume_series)
    if no_consensus:
        if task.get("consensusTasks"):
            consensus_task = task["consensusTasks"][0]
            task["labels"] = consensus_task.get("labels")
            task["labelsMap"] = consensus_task.get("labelsMap")
        dicom_rb_series(item_index_map, task, output, taxonomy, without_masks)
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
            super_truth: TaskType.OutputTask = {  # type: ignore
                "series": [{**series} for series in volume_series]
            }
            output["superTruth"] = super_truth
            if task.get("updatedBy"):
                output["superTruth"]["updatedBy"] = task["updatedBy"]
            if task.get("updatedAt"):
                output["superTruth"]["updatedAt"] = task["updatedAt"]
            dicom_rb_series(
                item_index_map, task, output["superTruth"], taxonomy, without_masks
            )

        consensus_tasks: List[TaskType.OutputTask] = [
            {"series": [{**series} for series in volume_series]}  # type: ignore
            for _ in range(len(task.get("consensusTasks", []) or []))
        ]
        output["consensusTasks"] = consensus_tasks
        for consensus_idx, output_consensus_task in enumerate(output["consensusTasks"]):
            consensus_task = task["consensusTasks"][consensus_idx]
            consensus_task["seriesInfo"] = task.get("seriesInfo")
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
                    score: TaskType.ConsensusScore = {}
                    if consensus_score.get("userId"):
                        score["secondaryUserId"] = consensus_score["userId"]

                    if consensus_score.get("assignee"):
                        score["secondaryUser"] = consensus_score["assignee"]
                    elif consensus_score.get("email"):
                        score["secondaryUserEmail"] = consensus_score["email"]

                    if consensus_score.get("score") is not None:
                        score["score"] = consensus_score["score"]
                    output_consensus_task["scores"].append(score)

            dicom_rb_series(
                item_index_map,
                consensus_task,
                output_consensus_task,
                taxonomy,
                without_masks,
            )

    return output
