"""Testing functions for Export."""


from typing import Dict
import numpy as np
from .public import Export

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
    "bike": 5,
    "truck": 6,
    "motor": 7,
}


def test_tax_class_id_map() -> None:
    """Test taxonomy classid map."""
    tax_map: Dict = {}
    tax = taxonomy_1["categories"][0]["children"]
    Export.tax_class_id_mapping(tax, tax_map)  # type: ignore
    assert tax_map == tax_map_1


def test_png_convert_simple() -> None:
    """Test converting to a simple png."""
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
        taxonomy["categories"][0]["children"], class_id_map, color_map  # type: ignore
    )

    task = {
        "labels": [
            {
                "category": [["object", "bus"]],
                "dpId": 123,
                "pixel": {
                    "imagesize": [10, 10],
                    "regions": [[[1, 1], [8, 1], [8, 8], [1, 8]]],
                    "holes": None,
                },
            }
        ]
    }
    color_mask = Export.convert_rbai_mask(task, class_id_map)
    assert (color_mask[1:8, 1:8, :] / color_map["bus"] == np.ones((7, 7, 3))).all()
