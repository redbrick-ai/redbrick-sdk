"""
Class representation of a taxonomy.
"""
from typing import Dict, Any, List


class Taxonomy2:
    """Class representation of a taxonomy."""

    def __init__(self, remote_tax: Dict[Any, Any]) -> None:
        """Constructor."""
        self.taxonomy = remote_tax
        self.name = remote_tax["name"]

        # Create class/id map objects
        class_id_map: Dict[str, int] = {}
        id_class_map: Dict[int, str] = {}
        self.class_id_map(
            tax=remote_tax["categories"][0]["children"],
            class_id_map=class_id_map,
            id_class_map=id_class_map,
        )
        self.taxonomy_class_id_map: Dict[str, int] = class_id_map
        self.taxonomy_id_class_map: Dict[int, str] = id_class_map

    def class_id_map(
        self, tax: List[Any], class_id_map: Dict[str, int], id_class_map: Dict[int, str]
    ) -> None:
        """Creates class/id maps recursively, vars are passed by reference."""
        if len(tax) == 0:
            return

        for elem in tax:
            class_id_map[elem["name"]] = elem["classId"]
            id_class_map[elem["classId"]] = elem["name"]
            self.class_id_map(elem["children"], class_id_map, id_class_map)

        return
