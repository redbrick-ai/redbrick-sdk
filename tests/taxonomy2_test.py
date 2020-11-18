"""
Test the taxonomy2 class.
"""

from redbrick.entity.taxonomy2 import Taxonomy2
import json

# DATA
TAXONOMY1 = {
    "taxonomy": {
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
}
TAXONOMY1_CLASS_ID = {
    "person": 0,
    "bicycle": 1,
    "car": 2,
    "motorbike": 3,
    "aeroplane": 4,
}
TAXONOMY1_ID_CLASS = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorbike",
    4: "aeroplane",
}


def test_always_passes() -> None:
    """Dummmy."""
    assert True


def test_init() -> None:
    """Test correct init."""
    # init
    Tax = Taxonomy2(remote_tax=TAXONOMY1["taxonomy"])

    # dummy check
    assert json.dumps(Tax.taxonomy) == json.dumps(TAXONOMY1["taxonomy"])

    # class/id map check
    assert json.dumps(Tax.taxonomy_class_id_map) == json.dumps(TAXONOMY1_CLASS_ID)
    assert json.dumps(Tax.taxonomy_id_class_map) == json.dumps(TAXONOMY1_ID_CLASS)


# DATA
TAXONOMY2 = {
    "taxonomy": {
        "name": "DEFAULT::YoloThings",
        "version": 1,
        "categories": [
            {
                "name": "object",
                "children": [
                    {
                        "name": "person",
                        "classId": 0,
                        "children": [
                            {
                                "name": "boy",
                                "classId": 5,
                                "children": [
                                    {"name": "young", "classId": 7, "children": []}
                                ],
                            },
                            {"name": "girl", "classId": 6, "children": []},
                        ],
                    },
                    {"name": "bicycle", "classId": 1, "children": []},
                    {"name": "car", "classId": 2, "children": []},
                    {"name": "motorbike", "classId": 3, "children": []},
                    {"name": "aeroplane", "classId": 4, "children": []},
                ],
            }
        ],
    }
}
TAXONOMY2_CLASS_ID = {
    "person": 0,
    "bicycle": 1,
    "car": 2,
    "motorbike": 3,
    "aeroplane": 4,
    "boy": 5,
    "girl": 6,
    "young": 7,
}
TAXONOMY2_ID_CLASS = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorbike",
    4: "aeroplane",
    5: "boy",
    6: "girl",
    7: "young",
}


def test_recursive() -> None:
    """Test tree taxonomy."""
    Tax = Taxonomy2(remote_tax=TAXONOMY2["taxonomy"])

    # Check maps
    assert Tax.taxonomy_id_class_map == TAXONOMY2_ID_CLASS
    assert Tax.taxonomy_class_id_map == TAXONOMY2_CLASS_ID
