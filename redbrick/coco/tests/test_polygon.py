"""Test methods for converting polygons for coco."""

from redbrick.coco.polygon import rb2coco_polygon, is_coco_polygon


def test_rb2coco_polygon_simple_square() -> None:
    """Test converting polygon rb label to coco label when the polygon is just a square."""
    # arrange
    label = {
        "label_id": "1234",
        "category": [["object", "bus"]],
        "polygon": [
            {"xnorm": 0, "ynorm": 0},
            {"xnorm": 1, "ynorm": 0},
            {"xnorm": 1, "ynorm": 1},
            {"xnorm": 0, "ynorm": 1},
        ],
    }

    # action
    result = rb2coco_polygon(label, 1, 1, 2, 100, 100)

    # assert
    assert result == {
        "id": 1,
        "image_id": 1,
        "category_id": 2,
        "bbox": [0, 0, 100, 100],
        "area": 10000,
        "iscrowd": 0,
        "segmentation": [[0, 0, 100, 0, 100, 100, 0, 100]],
    }
    assert is_coco_polygon(result)


def test_rb2coco_polygon_diamond() -> None:
    """Test converting polygon rb label to coco label when the polygon is a diamond."""
    # arrange
    label = {
        "label_id": "1234",
        "category": [["object", "bus"]],
        "polygon": [
            {"xnorm": 0.5, "ynorm": 0},
            {"xnorm": 1, "ynorm": 0.5},
            {"xnorm": 0.5, "ynorm": 1},
            {"xnorm": 0, "ynorm": 0.5},
        ],
    }

    # action
    result = rb2coco_polygon(label, 1, 1, 2, 100, 100)
    # assert
    assert result == {
        "id": 1,
        "image_id": 1,
        "category_id": 2,
        "bbox": [0, 0, 100, 100],
        "area": 5000,
        "iscrowd": 0,
        "segmentation": [[50, 0, 100, 50, 50, 100, 0, 50]],
    }
    assert is_coco_polygon(result)


def test_rb2coco_polygon_diamond_reverse_order() -> None:
    """
    Test converting polygon rb label to coco label with diamond shape.

    Reverse the direction to ensure area computation is consistent.
    """
    # arrange
    label = {
        "label_id": "1234",
        "category": [["object", "bus"]],
        "polygon": [
            {"xnorm": 0, "ynorm": 0.5},
            {"xnorm": 0.5, "ynorm": 1},
            {"xnorm": 1, "ynorm": 0.5},
            {"xnorm": 0.5, "ynorm": 0},
        ],
    }

    # action
    result = rb2coco_polygon(label, 1, 1, 2, 100, 100)

    # assert
    assert result == {
        "id": 1,
        "image_id": 1,
        "category_id": 2,
        "bbox": [0, 0, 100, 100],
        "area": 5000,
        "iscrowd": 0,
        "segmentation": [[0, 50, 50, 100, 100, 50, 50, 0]],
    }
    assert is_coco_polygon(result)
