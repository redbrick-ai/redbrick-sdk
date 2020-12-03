# mypy: ignore-errors
"""Test segmentation export functionality."""

from typing import Any
import filecmp
from unittest.mock import patch
import shutil
import os
import numpy as np  # type: ignore
import cv2

import redbrick
from tests.segmentation_test import remote_label5

from redbrick.entity.custom_group import CustomGroup
from redbrick.entity.datapoint import Image

# d8888b.  .d8b.  d888888b  .d8b.
# 88  `8D d8' `8b `~~88~~' d8' `8b
# 88   88 88ooo88    88    88ooo88
# 88   88 88~~~88    88    88~~~88
# 88  .8D 88   88    88    88   88
# Y8888D' YP   YP    YP    YP   YP

# Taxonomy
TAX = {
    "name": "DEFAULT::YoloThings",
    "version": 1,
    "categories": [
        {
            "name": "object",
            "children": [
                {"name": "person", "classId": 0, "children": []},
                {"name": "bicycle", "classId": 1, "children": []},
                {"name": "car", "classId": 2, "children": []},
                {"name": "motorbike", "classId": 3, "children": []},
                {"name": "aeroplane", "classId": 4, "children": []},
            ],
        }
    ],
}

# Image object
IMAGE = Image(
    org_id="123",
    label_set_name="abc",
    taxonomy={"person": 2, "car": 1, "background": 0},
    task_type="SEGMENTATION",
    remote_labels=remote_label5,
    dp_id="123",
    image_url="abc.png",
    image_url_not_signed="abc234.png",
    image_data=np.zeros((100, 100, 3)),
    created_by="123",
)

# Segmentation labelset mock
class MockImageSegmentation:
    """Image segmentation API mock."""

    def __init__(self) -> None:
        """Constructor."""
        return

    def get_datapoint_ids(self, org_id, label_set_name) -> Any:
        """Get data points ids."""
        return (
            ["1"],
            CustomGroup("SEGMENTATION", "IMAGE", TAX),
        )

    def get_datapoint(self, orgid, labelsetname, dpid, tasktype, taxonomy) -> Any:
        """Get the actual datapoint."""
        return IMAGE

    def get_members(self, org_id) -> Any:
        """get the members in the org."""
        x = {"123": "abc@def"}
        return x


@patch("redbrick.labelset.loader.RedBrickApi")
def test_export(mock: Any) -> None:
    """Test export."""
    # arrange
    mock.return_value = MockImageSegmentation()
    labelset = redbrick.labelset.LabelsetLoader(org_id="123", label_set_name="abc")

    # action
    cache_dir = labelset.export(format="redbrick")

    # assert
    expected_output = np.zeros([100, 100])
    expected_output[10:20, 10:20] = 1
    expected_output[12:18, 12:18] = 0
    expected_output[14:16, 14:16] = 2
    expected_output.dump("temp_test.dat")

    assert filecmp.cmp(
        "temp_test.dat", os.path.join(cache_dir, "abc234.png__export.dat")
    )

    # clean up
    shutil.rmtree(cache_dir)
    os.remove("temp_test.dat")


@patch("redbrick.labelset.loader.RedBrickApi")
def test_export_png(mock: Any) -> None:
    """Test export PNG Format."""
    # arrange
    mock.return_value = MockImageSegmentation()
    labelset = redbrick.labelset.LabelsetLoader(org_id="123", label_set_name="abc")

    print(
        "asdlfknadslkfnasldkfnalksdnfalskdnflkasdnflkasdnflkasdnflkasndflknsadklfnasldknflasdknfklasdnfklsadnfa",
        labelset.users,
    )
    # action
    cache_dir = labelset.export(format="redbrick-png")

    # assert
    expected_output = np.zeros([100, 100, 3])
    cmap = labelset[0].labels.color_map
    expected_output[10:20, 10:20, :] = cmap(1)
    expected_output[12:18, 12:18, :] = [0, 0, 0]
    expected_output[14:16, 14:16,] = cmap(2)
    # pylint: disable=no-member
    cv2.imwrite("temp_test.png", np.flip(expected_output, axis=2))

    assert filecmp.cmp(
        "temp_test.png", os.path.join(cache_dir, "abc234.png__export.png")
    )

    # clean up
    shutil.rmtree(cache_dir)
    os.remove("temp_test.png")
