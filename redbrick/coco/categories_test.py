"""Test functions for coco and rb categories."""

from .categories import rb2coco_categories_format, rb_get_class_id

taxonomy1 = {
    "name": "helloWorld",
    "version": 1,
    "attributes": [],
    "categories": [
        {
            "name": "object",
            "classId": -1,
            "children": [
                {"name": "bus", "classId": 0, "children": []},
                {"name": "traffic light", "classId": 1, "children": []},
                {"name": "traffic sign", "classId": 2, "children": []},
            ],
        }
    ],
}

taxonomy2 = {
    "name": "CocoStuff",
    "version": 1,
    "attributes": [],
    "categories": [
        {
            "name": "stuff",
            "classId": -1,
            "children": [
                {
                    "name": "outdoor",
                    "classId": 0,
                    "children": [
                        {
                            "name": "water",
                            "classId": 1,
                            "children": [
                                {"name": "water-other", "classId": 2, "children": [],},
                                {"name": "waterdrops", "classId": 3, "children": [],},
                                {"name": "sea", "classId": 4, "children": []},
                                {"name": "river", "classId": 5, "children": []},
                                {"name": "fog", "classId": 6, "children": []},
                            ],
                        },
                    ],
                }
            ],
        }
    ],
}


def test_ms_coco_categories_format() -> None:
    """Test converting into ms coco category format."""
    # arrange

    # action
    result = rb2coco_categories_format(taxonomy1)

    # asset
    assert result == [
        {"name": "bus", "id": 0, "supercategory": "object"},
        {"name": "traffic light", "id": 1, "supercategory": "object"},
        {"name": "traffic sign", "id": 2, "supercategory": "object"},
    ]


def test_ms_coco_categories_format_double_nested() -> None:
    """Test converting into ms coco category format."""
    # arrange

    # action
    result = rb2coco_categories_format(taxonomy2)

    # asset
    assert result == [
        {"name": "outdoor", "id": 0, "supercategory": "stuff"},
        {"name": "water", "id": 1, "supercategory": "outdoor"},
        {"name": "water-other", "id": 2, "supercategory": "water"},
        {"name": "waterdrops", "id": 3, "supercategory": "water"},
        {"name": "sea", "id": 4, "supercategory": "water"},
        {"name": "river", "id": 5, "supercategory": "water"},
        {"name": "fog", "id": 6, "supercategory": "water"},
    ]


def test_rb_get_class_id() -> None:
    """Test getting class id for rb category."""
    # arrange
    category = ["stuff", "outdoor", "water", "fog"]
    expected = 6

    # action
    result = rb_get_class_id(category, taxonomy2)

    # assert
    assert result == expected
