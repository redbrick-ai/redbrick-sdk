# mypy: ignore-errors
# pylint: skip-file

"""
Test the labelset module.
"""

import redbrick
import unittest
from typing import Any
from unittest.mock import patch, MagicMock
from redbrick.entity.custom_group import CustomGroup
from redbrick.tests.taxonomy2_test import TAXONOMY1
from .datapoint_test import IMAGE, VIDEO, VIDEO_CLASSIFY
import os
import numpy as np
import shutil
import json
import uuid


# d888888b .88b  d88.  .d8b.   d888b  d88888b
#   `88'   88'YbdP`88 d8' `8b 88' Y8b 88'
#    88    88  88  88 88ooo88 88      88ooooo
#    88    88  88  88 88~~~88 88  ooo 88~~~~~
#   .88.   88  88  88 88   88 88. ~8~ 88.
# Y888888P YP  YP  YP YP   YP  Y888P  Y88888P


class Mock_Image:
    """Mocking RedBrickApi for images."""

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
    assert os.listdir(os.path.join(cache_dir, "obj_train_data")) == [
        IMAGE.image_url_not_signed[0:-4] + ".png",
        IMAGE.image_url_not_signed[0:-4] + ".txt",
    ]
    shutil.rmtree(cache_dir)


# db    db d888888b d8888b. d88888b  .d88b.
# 88    88   `88'   88  `8D 88'     .8P  Y8.
# Y8    8P    88    88   88 88ooooo 88    88
# `8b  d8'    88    88   88 88~~~~~ 88    88
#  `8bd8'    .88.   88  .8D 88.     `8b  d8'
#    YP    Y888888P Y8888D' Y88888P  `Y88P'


class Mock_Video:
    """Mocking RedBrickApi for video."""

    def __init__(self):
        return

    def get_datapoint_ids(self, org_id, label_set_name):
        return (
            ["1", "2"],
            CustomGroup("BBOX", "VIDEO", TAXONOMY1["taxonomy"]),
        )

    def get_datapoint(self, orgid, labelsetname, dpid, tasktype, taxonomy):
        return VIDEO


class Mock_Video_Classify:
    """Mocking RedBrickApi for video."""

    def __init__(self):
        return

    def get_datapoint_ids(self, org_id, label_set_name):
        return (
            ["1", "2"],
            CustomGroup("CLASSIFY", "VIDEO", TAXONOMY1["taxonomy"]),
        )

    def get_datapoint(self, orgid, labelsetname, dpid, tasktype, taxonomy):
        VIDEO_CLASSIFY.video_name = dpid
        return VIDEO_CLASSIFY


@patch("redbrick.entity.export.export_video.url_to_image")
@patch("redbrick.labelset.loader.RedBrickApi")
def test_labelset_export_image(mock: Any, url_to_image: Any) -> None:
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


@patch("redbrick.entity.export.export_video.url_to_image")
@patch("redbrick.labelset.loader.RedBrickApi")
def test_labelset_export_video_clasify(mock: Any, url_to_image: Any) -> None:
    """Test labelset export for images."""
    mock.return_value = Mock_Video_Classify()
    url_to_image.return_value = np.zeros((10, 10, 3))

    labelset = redbrick.labelset.LabelsetLoader(org_id="123", label_set_name="abc")
    cache_dir = labelset.export(format="redbrick")

    assert os.path.isdir(cache_dir)

    files = os.listdir(cache_dir)
    assert len(files) == 2
    assert files == ["1", "2"]
    shutil.rmtree(cache_dir)


@patch("redbrick.entity.export.export_video.url_to_image")
@patch("redbrick.labelset.loader.RedBrickApi")
def test_labelset_export_video_clasify_json(mock: Any, url_to_image: Any) -> None:
    """Test labelset export for images."""
    mock.return_value = Mock_Video_Classify()
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
