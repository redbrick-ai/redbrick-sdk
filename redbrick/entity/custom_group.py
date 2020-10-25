from typing import List, Optional
import json
from .taxonomy import TaxonomyEntry
from typing import Dict, Any


class CustomGroup:
    def __init__(
        self, task_type: str, data_type: str, taxonomy: Dict[Any, Any]
    ) -> None:
        """Construct a CustomGroup object."""
        self.task_type = task_type
        self.data_type = data_type

        tax_map: Dict[str, int] = {}
        self.trav_tax(taxonomy["categories"][0], tax_map)
        self.taxonomy = tax_map

    def trav_tax(self, taxonomy: Dict[Any, Any], tax_map: Dict[str, int]) -> None:
        """Traverse the taxonomy tree structure, and fill the taxonomy mapper object."""
        children = taxonomy["children"]
        if len(children) == 0:
            return

        for child in children:
            tax_map[child["name"]] = child["classId"]
            self.trav_tax(child, tax_map)
