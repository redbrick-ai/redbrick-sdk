"""Taxonomy utilities."""
from typing import Dict


def format_taxonomy(taxonomy: Dict) -> Dict:
    """Parse taxonomy object."""
    keys = ["orgId", "name", "createdAt", "archived", "isNew"]
    if taxonomy["isNew"]:
        keys.extend(
            [
                "taxId",
                "studyClassify",
                "seriesClassify",
                "instanceClassify",
                "objectTypes",
            ]
        )
    else:
        keys.extend(
            [
                "version",
                "categories",
                "attributes",
                "taskCategories",
                "taskAttributes",
                "colorMap",
            ]
        )

    return {key: taxonomy[key] for key in keys}
