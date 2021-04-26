"""Utilities for convert labels to COCO format."""
from typing import List, Optional


def coco_categories_format(taxonomy: dict) -> List[dict]:
    """Convert to coco categories format."""
    root = taxonomy["categories"][0]

    output: List[dict] = []

    def recurse(cat: dict) -> None:
        """Recurse and add child entries to output."""
        for child in cat.get("children", []):
            temp = {
                "name": child["name"],
                "id": child["classId"] + 1,
                "supercategory": cat["name"],
            }

            output.append(temp)
            recurse(child)

    recurse(root)

    return output


def _get_label_class_id(label_category: List[str], taxonomy: dict) -> int:
    """Get map of taxonomy categories."""
    categories = taxonomy["categories"]
    assert len(categories) == 1

    def find_name_in_categories(
        temp_categories: List[dict], name: str
    ) -> Optional[dict]:
        for cat in temp_categories:
            if cat["name"] == name:
                return cat
        return None

    for cat in label_category:
        new_root = find_name_in_categories(categories, cat)
        if new_root:
            categories = new_root.get("children")

    if new_root:
        class_id: int = new_root["classId"]
        return class_id
    else:
        raise Exception("Couldn't find class")


def _convert_coco_to_normalized_bbox(bbox: List, width: int, height: int) -> dict:
    # Current output is already normalized.
    xnorm = bbox[0]  # / (width - 1)
    ynorm = bbox[1]  # / (height - 1)
    wnorm = bbox[2]  # / (width - 1)
    hnorm = bbox[3]  # / (height - 1)

    if xnorm < 0:
        xnorm = 0
    if ynorm < 0:
        ynorm = 0
    if xnorm + wnorm > 1:
        wnorm = 1 - xnorm
    if ynorm + hnorm > 1:
        hnorm = 1 - ynorm

    return {
        "xnorm": xnorm,
        "ynorm": ynorm,
        "wnorm": wnorm,
        "hnorm": hnorm,
    }


def _convert_normalized_bbox_to_coco(
    bbox_norm: dict, width: int, height: int
) -> List[float]:
    return [
        bbox_norm["xnorm"] * (width - 1),
        bbox_norm["ynorm"] * (height - 1),
        bbox_norm["wnorm"] * (width - 1),
        bbox_norm["hnorm"] * (height - 1),
    ]


def coco_labels_format(
    label: dict, img_width: int, img_height: int, taxonomy: dict, dp_id: str,
) -> dict:
    """Convert internal rb format to ms coco format."""
    category = label["category"]
    class_id = _get_label_class_id(category[0], taxonomy)
    _label = {
        "image_id": dp_id,
        "category_id": class_id + 1,
        "area": 0,
        "bbox": [],
        "iscrowd": 0,
    }
    if label.get("bbox2d"):
        new_bbox = _convert_normalized_bbox_to_coco(
            label["bbox2d"], img_width, img_height
        )
        _label.update({"bbox": new_bbox})

    elif label.get("polygon"):
        seg = [list(sum(label["pixel"]["regions"][0][0], ()))]
        _label.update({"segmentation": seg})

    return _label


def coco_image_format(
    img_width: int, img_height: int, file_name: str, dp_id: str
) -> dict:
    """Convert image to coco format."""
    return {
        "file_name": file_name,
        "height": img_height,
        "width": img_width,
        "id": dp_id,
        "dp_id": dp_id,
    }
