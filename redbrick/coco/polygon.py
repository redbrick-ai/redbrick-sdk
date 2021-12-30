"""Convert between rb and coco for polygon labels."""

from typing import Dict, List
from shapely.geometry import Polygon  # type: ignore
from shapely.validation import make_valid  # type: ignore


def _create_bbox(polygon: Polygon) -> List[int]:
    """Get a bounding box entry in a single COCO annotation field for a polygon."""
    bounds = polygon.bounds

    x_min = bounds[0]
    y_min = bounds[1]
    x_max = bounds[2]
    y_max = bounds[3]

    width = x_max - x_min
    height = y_max - y_min

    return [x_min, y_min, width, height]


def _get_polygon(segmentation: List[int]) -> Polygon:
    """Get shapely polygon object."""
    x_pos = []
    y_pos = []

    for idx, coord in enumerate(segmentation):
        if idx % 2 == 0:
            x_pos += [coord]
        else:
            y_pos += [coord]

    polygon = Polygon(zip(x_pos, y_pos))

    return polygon if polygon.is_valid else make_valid(polygon)


def _get_segmentation(polygon: List[Dict], width: int, height: int) -> List[int]:
    """Convert RedBrick polygon to coco segmentation field."""
    segment = []
    for point in polygon:
        segment += [
            int(point["xnorm"] * width),
            int(point["ynorm"] * height),
        ]

    return segment


def rb2coco_polygon(
    rb_label: Dict,
    label_id: int,
    image_id: int,
    category_id: int,
    width: int,
    height: int,
) -> Dict:
    """Convert rb polygon to coco polygon."""
    assert rb_label.get("polygon")

    segmentation = _get_segmentation(rb_label["polygon"], width, height)
    polygon = _get_polygon(segmentation)
    bbox = _create_bbox(polygon)

    return {
        "id": label_id,
        "image_id": image_id,
        "category_id": category_id,
        "bbox": bbox,
        "iscrowd": 0,
        "area": int(polygon.area),
        "segmentation": [segmentation],
    }


def is_coco_polygon(coco_label: Dict) -> bool:
    """Check if a given label is a valid polygon only label."""
    has_bbox = "bbox" in coco_label and len(coco_label["bbox"]) == 4
    has_segment = len(coco_label.get("segmentation", [])) > 0
    no_keypoints = not coco_label.get("keypoints")
    return has_bbox and has_segment and no_keypoints


def coco2rb_polygon(
    coco_label: Dict, category: List[List[str]], width: int, height: int
) -> Dict:
    """Convert coco polygon to rb polygon."""
    raise NotImplementedError(coco_label, category, width, height)
