"""Methods to handle converting category formats."""
from typing import Dict, List, Optional


def rb2coco_categories_format(taxonomy: Dict) -> List[Dict]:
    """Convert to ms_coco categories format."""
    root = taxonomy["categories"][0]

    output: List[Dict] = []

    def recurse(cat: Dict) -> None:
        """Recurse and add child entries to output."""
        for child in cat.get("children", []):
            print(child)
            temp = {
                "name": child["name"],
                "id": child["classId"],
                "supercategory": cat["name"],
            }

            output.append(temp)
            recurse(child)

    recurse(root)

    return output


def rb_get_class_id(label_category: List[str], taxonomy: dict) -> int:
    """Get classId for label using taxonomy."""
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
