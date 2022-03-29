"""Testing functions for Export."""


import sys
from typing import Dict
import copy

import numpy as np
from redbrick.export.public import Export

taxonomy_1 = {
    "categories": [
        {
            "name": "object",
            "children": [
                {
                    "name": "bus",
                    "classId": 0,
                    "children": [
                        {"name": "motor", "classId": 6, "children": []},
                    ],
                },
                {"name": "traffic light", "classId": 1, "children": []},
                {"name": "traffic sign", "classId": 2, "children": []},
                {
                    "name": "person",
                    "classId": 3,
                    "children": [
                        {"name": "bike", "classId": 4, "children": []},
                        {"name": "truck", "classId": 5, "children": []},
                    ],
                },
            ],
        }
    ],
}
tax_map_1 = {
    "bus": 1,
    "traffic light": 2,
    "traffic sign": 3,
    "person": 4,
    "person::bike": 5,
    "person::truck": 6,
    "bus::motor": 7,
}


def test_tax_class_id_map() -> None:
    """Test taxonomy classid map."""
    class_id: Dict = {}
    color_map: Dict = {}
    tax: Dict = taxonomy_1["categories"][0]["children"]  # type: ignore
    Export.tax_class_id_mapping(
        [taxonomy_1["categories"][0]["name"]], tax, class_id, color_map
    )
    assert class_id == tax_map_1


def test_png_convert_simple() -> None:
    """Test converting to a simple png."""
    if sys.platform not in ("linux", "darwin"):
        # Don't run this test for windows, w/o rasterio will fail.
        assert True
        return

    taxonomy = {
        "categories": [
            {
                "name": "object",
                "children": [{"name": "bus", "classId": 0, "children": []}],
            }
        ]
    }
    class_id_map: Dict = {}
    color_map: Dict = {}
    Export.tax_class_id_mapping(
        [taxonomy["categories"][0]["name"]],
        taxonomy["categories"][0]["children"],  # type: ignore
        class_id_map,
        color_map,
    )

    task = {
        "labels": [
            {
                "category": [["object", "bus"]],
                "pixel": {
                    "imagesize": [10, 10],
                    "regions": [[[1, 1], [8, 1], [8, 8], [1, 8]]],
                    "holes": None,
                },
            }
        ]
    }
    color_mask = Export.convert_rbai_mask(
        task["labels"], class_id_map, color_map, False, 30
    )
    assert (color_mask[1:8, 1:8, :] / color_map["bus"] == np.ones((7, 7, 3))).all()


def test_fill_holes_simple() -> None:
    """Tests the fill holes operation."""
    mask = np.zeros((10, 10))
    mask[2:7, 2:7] = 1
    mask[3:6, 3:6] = 0

    mask_true = np.zeros((10, 10))
    mask_true[2:7, 2:7] = 1
    mask_filled = Export.fill_mask_holes(mask, 30)

    assert (mask_filled == mask_true).all()

    mask_filled_2 = Export.fill_mask_holes(mask, 4)
    assert (mask_filled_2 == mask).all()


def test_fill_holes_big_and_small() -> None:
    """Test the fill holes operation, for big and small holes."""
    mask = np.ones((50, 50))
    mask[20:40, 20:40] = 0
    mask_true = copy.deepcopy(mask)
    mask[2:7, 2:7] = 0

    mask_filled = Export.fill_mask_holes(mask, 26)
    assert (mask_filled == mask_true).all()
