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


def coco_labels_format(label: dict, taxonomy: dict, dp_id: str,) -> dict:
    """Convert internal rb format to ms coco format."""
    category = label["category"]
    class_id = _get_label_class_id(category[0], taxonomy)
    _label = {
        "image_id": dp_id,
        "category_id": class_id + 1,
        "area": 0,
        "bbox": [],
        "iscrowd": 0,
        "segmentation": [list(sum(label["pixel"]["regions"][0][0], ()))],
    }
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
