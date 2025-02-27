"""Label utils."""

from typing import Dict, List, Literal

from redbrick.types.taxonomy import Attribute, Taxonomy


def process_labels(labels: List[Dict], taxonomy: Taxonomy) -> List[Dict]:
    """Map label attribute values."""
    if not labels or not taxonomy.get("isNew"):
        return labels

    classify_map: Dict[Literal["STUDY", "SERIES", "INSTANCE"], Dict[int, Attribute]] = {
        "STUDY": {
            attr["attrId"]: attr for attr in (taxonomy.get("studyClassify") or [])
        },
        "SERIES": {
            attr["attrId"]: attr for attr in (taxonomy.get("seriesClassify") or [])
        },
        "INSTANCE": {
            attr["attrId"]: attr for attr in (taxonomy.get("instanceClassify") or [])
        },
    }

    for label in labels:
        attr_map = {}
        if label.get("studyclassify"):
            attr_map = classify_map.get("STUDY", {})
        elif label.get("seriesclassify"):
            attr_map = classify_map.get("SERIES", {})
        elif label.get("instanceclassify"):
            attr_map = classify_map.get("INSTANCE", {})
        else:
            object_type = next(
                (
                    obj
                    for obj in (taxonomy.get("objectTypes") or [])
                    if obj["classId"] == label.get("classid")
                ),
                None,
            )
            if object_type:
                label["category"] = object_type["category"]
                attr_map = {
                    attr["attrId"]: attr
                    for attr in (object_type.get("attributes") or [])
                }

        for attribute in label.get("attributes") or []:
            if attribute.get("attrid") is not None:
                attr = attr_map.get(attribute["attrid"])
                if attr:
                    deserialize_attribute(attribute, attr)

    return labels


def deserialize_attribute(attribute: Dict, attr: Attribute) -> None:
    """Deserialize the derived properties."""
    options: Dict[int, str] = {
        option["optionId"]: option["name"] for option in (attr.get("options") or [])
    }
    attribute["name"] = attr["name"]
    if attr["attrType"] == "SELECT":
        attribute["value"] = (
            options.get(attribute["optionid"])
            if isinstance(attribute.get("optionid"), int)
            else None
        )
    elif attr["attrType"] == "MULTISELECT":
        values = [
            options.get(opt_id)
            for opt_id in (
                attribute["optionid"]
                if isinstance(attribute.get("optionid"), list)
                else []
            )
        ]
        if not any(value is None for value in values):
            attribute["value"] = values
