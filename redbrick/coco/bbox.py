"""Convert between rb and coco for bbox labels."""

from typing import Dict, List


def rb2coco_bbox(
    rb_label: Dict,
    label_id: int,
    image_id: int,
    category_id: int,
    width: int,
    height: int,
) -> Dict:
    """Convert rb bbox to coco bbox."""
    assert rb_label["bbox2d"]

    xnorm = rb_label["bbox2d"]["xnorm"]
    ynorm = rb_label["bbox2d"]["ynorm"]
    wnorm = rb_label["bbox2d"]["wnorm"]
    hnorm = rb_label["bbox2d"]["hnorm"]
    return {
        "id": label_id,
        "image_id": image_id,
        "category_id": category_id,
        "bbox": [
            int(xnorm * width),
            int(ynorm * height),
            int(wnorm * width),
            int(hnorm * height),
        ],
        "iscrowd": 0,
        "area": int(wnorm * width) * int(hnorm * height),
        "segmentation": [],
    }


def is_coco_bbox(coco_label: Dict) -> bool:
    """Check if given label is a valid "bbox" only label."""
    has_bbox = "bbox" in coco_label and len(coco_label["bbox"]) == 4
    no_segment = not coco_label.get("segmentation")
    no_keypoints = not coco_label.get("keypoints")
    return has_bbox and no_segment and no_keypoints


def coco2rb_bbox(
    coco_label: Dict, category: List[List[str]], width: int, height: int
) -> Dict:
    """Convert coco bbox to rb bbox."""
    assert is_coco_bbox(coco_label)

    xnorm = coco_label["bbox"][0] / width
    ynorm = coco_label["bbox"][1] / height
    wnorm = coco_label["bbox"][2] / width
    hnorm = coco_label["bbox"][3] / height

    xnorm = max(xnorm, 0)
    ynorm = max(ynorm, 0)
    if xnorm + wnorm > 1:
        wnorm = 1 - xnorm
    if ynorm + hnorm > 1:
        hnorm = 1 - ynorm

    return {
        "category": category,
        "bbox2d": {
            "xnorm": xnorm,
            "ynorm": ynorm,
            "wnorm": wnorm,
            "hnorm": hnorm,
        },
    }
