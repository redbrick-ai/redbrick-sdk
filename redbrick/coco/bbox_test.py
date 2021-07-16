"""Tests for bbox conversion."""


from .bbox import rb2coco_bbox, coco2rb_bbox, is_coco_bbox


def test_rb2coco_bbox() -> None:
    """Test converting from rb bbox to coco bbox."""
    # arrange
    label = {
        "label_id": "1234",
        "category": [["object", "bus"]],
        "bbox2d": {"xnorm": 0, "ynorm": 0, "wnorm": 1, "hnorm": 1},
    }

    # action
    result = rb2coco_bbox(label, 1, 1, 2, 100, 100)
    result2 = coco2rb_bbox(result, [["object", "bux"]], 100, 100)
    result3 = rb2coco_bbox(result2, 1, 1, 2, 100, 100)
    # assert
    assert result == {
        "id": 1,
        "image_id": 1,
        "category_id": 2,
        "bbox": [0, 0, 100, 100],
        "area": 10000,
        "iscrowd": 0,
        "segmentation": [],
    }
    assert result == result3, "Conversion is not consistent/symmetric"
    assert is_coco_bbox(result)


def test_is_coco_bbox() -> None:
    """Test if given coco label is an rb bbox."""
    assert is_coco_bbox(
        {
            "image_id": 1,
            "category_id": 2,
            "bbox": [0, 0, 100, 100],
            "area": 10000,
            "iscrowd": 0,
            "segmentation": [],
        }
    )
    assert not is_coco_bbox(
        {
            "image_id": 1,
            "category_id": 2,
            "bbox": [0, 0, 100, 100],
            "area": 10000,
            "iscrowd": 0,
            "segmentation": [1, 1, 1, 1],
        }
    )
    assert not is_coco_bbox(
        {
            "image_id": 1,
            "category_id": 2,
            "bbox": [0, 0, 100, 100],
            "area": 10000,
            "iscrowd": 0,
            "segmentation": [],
            "keypoints": [2, 1, 0],
        }
    )
