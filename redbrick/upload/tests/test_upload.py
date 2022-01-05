"""Tests for upload module."""
import json
import sys
from typing import List, Dict

from uuid import uuid4
import matplotlib.pyplot as plt
import pytest

from redbrick.common.enums import StorageMethod
from redbrick.utils.files import get_file_type
from redbrick.upload.public import Upload
from redbrick.tests.conftest import *  # pylint: disable=wildcard-import, unused-wildcard-import


def test_mask_rbai() -> None:
    """Test mask to polygon conversion."""
    if sys.platform not in ("linux", "darwin"):
        # Don't run this test for windows, w/o rasterio will fail.
        assert True
        return
    # read mask that was generated by rbai export
    # i.e. rbai polygon -> png mask format
    mask = plt.imread(
        "redbrick/upload/mask_test/88664c8f-c6f8-4d5a-918e-41d8441a4509.png"
    )
    with open(
        "redbrick/upload/mask_test/class_map.json", "r", encoding="utf-8"
    ) as file:
        class_map = json.load(file)

    # convert the mask to rbai polygon
    dp_entry = Upload.mask_to_rbai(mask, class_map, "items123", "name123")

    # read original rbai polygon format
    with open(
        "redbrick/upload/mask_test/redbrick_export_segment.json", "r", encoding="utf-8"
    ) as file:
        datapoints = json.load(file)
    dp_entry_real = datapoints[0]

    # compare the two polygon formats to confirm mask -> polygon is correct
    for label_real in dp_entry_real["labels"]:
        for label in dp_entry["labels"]:
            if label_real["category"] == label["category"]:
                assert (
                    label_real["pixel"]["regions"].sort()
                    == label["pixel"]["regions"].sort()
                )

                if label_real["pixel"]["holes"]:
                    assert (
                        label_real["pixel"]["holes"].sort()
                        == label["pixel"]["holes"].sort()
                    )


def test_file_type_extraction() -> None:
    """Tests the extraction of MIME file type."""
    filepath = "folder/subfolder/image.png"
    filetype = get_file_type(filepath)
    assert filetype[0] == "png" and filetype[1] == "image/png"


def test_file_type_extraction_invalid() -> None:
    """Check invalid file extraction."""
    filepath = "folder/subfolder/image.csv"
    try:
        get_file_type(filepath)
        assert False
    except ValueError as error:
        assert type(error).__name__ == "ValueError"


def test_items_validity() -> None:
    """Check invalid items."""
    # pylint: disable=protected-access
    file_name = f"{uuid4()}.png"
    with open(file_name, "w", encoding="utf-8") as file_:
        file_.write("test")

    items = [2, "", "missing.txt", file_name]
    invalid = Upload._check_validity_of_items(items)  # type: ignore
    os.remove(file_name)
    assert len(invalid) == len(items) - 1


@pytest.mark.slow
def test_invalid_upload_object(project: RBProject) -> None:
    """Check invalid item list upload."""
    tasks: List[Dict] = [
        {},
        {"name": None},
        {"items": []},
        {"name": "test"},
        {"name": "test", "items": ""},
        {"name": "test", "items": []},
        {"name": "test", "items": [0]},
        {
            "name": "test",
            "items": [
                "https://datasets.redbrickai.com/bccd/BloodImage_00000.jpg",
                "https://datasets.redbrickai.com/bccd/BloodImage_00000.jpg",
            ],
        },
        {
            "name": "test",
            "items": ["https://datasets.redbrickai.com/bccd/BloodImage_00000.jpg"],
            "labels": {},
        },
        {
            "name": str(uuid4()),
            "items": ["https://datasets.redbrickai.com/bccd/BloodImage_00000.jpg"],
        },
    ]
    task_objects = project.upload.create_datapoints(StorageMethod.PUBLIC, tasks)
    assert (
        len(task_objects) == len(tasks)
        and len(list(filter(lambda task: "response" in task, task_objects))) == 1
    )