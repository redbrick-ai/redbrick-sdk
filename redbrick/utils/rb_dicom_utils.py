"""Utilities for working with datapoint objects."""

from typing import Dict, List
import json
from copy import deepcopy

from redbrick.types import task as TaskType
from redbrick.utils.logging import logger
from redbrick.utils.rb_label_utils import convert_datapoint_classifications


def dicom_dp_format(datapoint: Dict) -> Dict:
    """Get new dicom rb datapoint format."""
    # pylint: disable=too-many-branches, too-many-statements, too-many-locals, unused-argument

    if not datapoint.get("seriesInfo"):
        datapoint["seriesInfo"] = [{}]
    if any(not series.get("itemsIndices") for series in datapoint["seriesInfo"]):
        datapoint["seriesInfo"][0]["itemsIndices"] = list(
            range(len(datapoint["items"]))
        )
        if len(datapoint["seriesInfo"]) > 1:
            logger.warning(
                f"{datapoint['dpId']} - Putting all items in first series since split is unknown"
            )
            for series in datapoint["seriesInfo"][1:]:
                series["itemsIndices"] = []

    output: Dict = {"dpId": datapoint["dpId"], "name": "", "series": []}

    if datapoint.get("name"):
        output["name"] = datapoint["name"]
    elif datapoint.get("items"):
        output["name"] = datapoint["items"][0]

    if datapoint.get("priority") is not None:
        output["priority"] = datapoint["priority"]

    if datapoint.get("createdBy"):
        output["createdBy"] = datapoint["createdBy"]

    if datapoint.get("createdAt"):
        output["createdAt"] = datapoint["createdAt"]

    if datapoint.get("attributes"):
        output["classification"] = convert_datapoint_classifications(
            json.loads(datapoint["attributes"])
            if isinstance(datapoint["attributes"], str)
            else datapoint["attributes"]
        )

    if datapoint.get("metaData"):
        output["metaData"] = (
            json.loads(datapoint["metaData"])
            if isinstance(datapoint["metaData"], str)
            else datapoint["metaData"]
        )

    volume_series: List[TaskType.Series] = [
        {} for _ in range(len(datapoint["seriesInfo"]))
    ]
    item_index_map: Dict[int, int] = {}
    for volume_index, series_info in enumerate(datapoint["seriesInfo"]):
        series = volume_series[volume_index]
        if series_info.get("name"):
            series["name"] = series_info["name"]  # type: ignore

        series_meta_data = series_info.get("metaData")
        if isinstance(series_meta_data, str):
            series["metaData"] = json.loads(series_meta_data)

        series["items"] = []
        for item_index in series_info["itemsIndices"]:
            item_index_map[item_index] = volume_index
            series["items"].append(datapoint["itemsPresigned"][item_index])  # type: ignore

    output["series"] = deepcopy(volume_series)

    if datapoint.get("archived"):
        output["archived"] = datapoint["archived"]

    if datapoint.get("cohorts"):
        output["cohorts"] = [cohort["name"] for cohort in datapoint["cohorts"]]

    return output
