# mypy: ignore-errors
# pylint: skip-file
"""
Test the labelset module.
"""

from typing import Any
from unittest.mock import patch
import shutil
import json
import os
import matplotlib.pyplot as plt
import numpy as np

import redbrick
from redbrick.entity.custom_group import CustomGroup
from .taxonomy2_test import TAXONOMY1
from .video_test import VIDEO, VIDEO_CLASSIFY, VIDEO_BBOX_REAL
from .image_test import IMAGE


# d888888b .88b  d88.  .d8b.   d888b  d88888b
#   `88'   88'YbdP`88 d8' `8b 88' Y8b 88'
#    88    88  88  88 88ooo88 88      88ooooo
#    88    88  88  88 88~~~88 88  ooo 88~~~~~
#   .88.   88  88  88 88   88 88. ~8~ 88.
# Y888888P YP  YP  YP YP   YP  Y888P  Y88888P


class Mock_Image:
    def __init__(self):
        return

    def get_datapoint_ids(self, org_id, label_set_name):
        return (
            ["1", "2"],
            CustomGroup("BBOX", "IMAGE", TAXONOMY1["taxonomy"]),
        )

    def get_datapoint(self, orgid, labelsetname, dpid, tasktype, taxonomy):
        return IMAGE


@patch("redbrick.labelset.loader.RedBrickApi")
def test_labelset_init(mock: Any) -> None:
    """Test init of labelset."""

    mock.return_value = Mock_Image()
    labelset = redbrick.labelset.LabelsetLoader(org_id="123", label_set_name="abc")
    assert labelset.task_type == "BBOX"
    assert len(labelset.dp_ids) == 2


@patch("redbrick.labelset.loader.RedBrickApi")
def test_labelset_export_image(mock: Any) -> None:
    """Test labelset export for images."""
    mock.return_value = Mock_Image()

    labelset = redbrick.labelset.LabelsetLoader(org_id="123", label_set_name="abc")
    cache_dir = labelset.export(format="redbrick")

    assert os.path.isdir(cache_dir)
    assert os.listdir(os.path.join(cache_dir, "obj_train_data")).sort() == [
        IMAGE.image_url_not_signed[0:-4] + ".png",
        IMAGE.image_url_not_signed[0:-4] + ".txt",
    ].sort()
    shutil.rmtree(cache_dir)


# db    db d888888b d8888b. d88888b  .d88b.
# 88    88   `88'   88  `8D 88'     .8P  Y8.
# Y8    8P    88    88   88 88ooooo 88    88
# `8b  d8'    88    88   88 88~~~~~ 88    88
#  `8bd8'    .88.   88  .8D 88.     `8b  d8'
#    YP    Y888888P Y8888D' Y88888P  `Y88P'


class Mock_Video:
    """Mocking RedBrickApi for video."""

    def __init__(self, data=VIDEO, tasktype="BBOX", num_pts=2):
        self.data = data
        self.task_type = tasktype
        self.dps = [str(i) for i in range(num_pts)]

    def get_datapoint_ids(self, org_id, label_set_name):
        return (
            self.dps,
            CustomGroup(self.task_type, "VIDEO", TAXONOMY1["taxonomy"]),
        )

    def get_datapoint(self, orgid, labelsetname, dpid, tasktype, taxonomy):
        if tasktype == "CLASSIFY":
            self.data.video_name = dpid
        return self.data


@patch("redbrick.export.export_video.url_to_image")
@patch("redbrick.labelset.loader.RedBrickApi")
def test_labelset_export_video(mock: Any, url_to_image: Any) -> None:
    """Test labelset export for images."""
    mock.return_value = Mock_Video()
    url_to_image.return_value = np.zeros((10, 10, 3))

    labelset = redbrick.labelset.LabelsetLoader(org_id="123", label_set_name="abc")
    cache_dir = labelset.export(format="redbrick")

    assert os.path.isdir(cache_dir)

    outdir = []
    for item in VIDEO.items_list_not_signed:
        outdir += [(item[0:-4] + ".txt").replace("/", "_").replace(":", "_")]
        outdir += [(item[0:-4] + ".png").replace("/", "_").replace(":", "_")]

    assert os.listdir(os.path.join(cache_dir, "obj_train_data")).sort() == outdir.sort()
    shutil.rmtree(cache_dir)


@patch("redbrick.export.export_video.url_to_image")
@patch("redbrick.labelset.loader.RedBrickApi")
def test_labelset_export_video_clasify(mock: Any, url_to_image: Any) -> None:
    """Test labelset export for images."""
    mock.return_value = Mock_Video(data=VIDEO_CLASSIFY, tasktype="CLASSIFY")
    url_to_image.return_value = np.zeros((10, 10, 3))

    labelset = redbrick.labelset.LabelsetLoader(org_id="123", label_set_name="abc")
    cache_dir = labelset.export(format="redbrick")

    assert os.path.isdir(cache_dir)

    files = os.listdir(cache_dir)
    assert len(files) == 2
    assert files.sort() == mock.return_value.dps.sort()
    shutil.rmtree(cache_dir)


@patch("redbrick.export.export_video.url_to_image")
@patch("redbrick.labelset.loader.RedBrickApi")
def test_labelset_export_video_clasify_json(mock: Any, url_to_image: Any) -> None:
    """Test labelset export for images."""
    mock.return_value = Mock_Video(data=VIDEO_CLASSIFY, tasktype="CLASSIFY")
    url_to_image.return_value = np.zeros((10, 10, 3))

    labelset = redbrick.labelset.LabelsetLoader(org_id="123", label_set_name="abc")
    cache_dir = labelset.export(format="redbrick-json")

    assert os.path.isdir(cache_dir)

    files = os.listdir(cache_dir)
    assert len(files) == 1

    # open the json file
    with open(os.path.join(cache_dir, files[0]), "r") as file:
        labels = json.load(file)

    shutil.rmtree(cache_dir)


@patch("redbrick.entity.datapoint.video.url_to_image")
@patch("redbrick.labelset.loader.RedBrickApi")
def test_labelset_showdata_video(mock: Any, url_to_image: Any) -> None:
    """Test labelset export for images."""
    mock.return_value = Mock_Video(data=VIDEO_BBOX_REAL, num_pts=20)
    url_to_image.return_value = np.ones((10, 10, 3)) * 0.5

    labelset = redbrick.labelset.LabelsetLoader(org_id="123", label_set_name="abc")

    plt.ion()  # make plt.show non blocking
    labelset.show_data()
    plt.close()
