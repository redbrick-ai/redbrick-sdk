"""Generate Iterator for the labelset."""

from typing import Any, Dict, Iterable, List

from redbrick.api import RedBrickApi
from redbrick.logging import print_error


class LabelsetIterator:
    """Construct Labelset Iterator."""

    def __init__(self, org_id: str, label_set_name: str) -> None:
        self.api = RedBrickApi()

        self.cursor = None
        self.datapointsBatch = None
        self.datapointsBatchIndex = None

        self.org_id = org_id
        self.label_set_name = label_set_name

        self.valid_task_types: List = ["SEGMENTATION", "POLYGON", "MULTI"]

        self.customGroup = self._get_custom_group()
        self.taxonomy = self.customGroup["taxonomy"]
        self.datapointCount = self.customGroup["datapointCount"]
        self.taxonomy_segm = self._get_taxonomy_segmentation()

    def _get_custom_group(self) -> None:
        return self.api.get_datapoints_paged(
            org_id=self.org_id, label_set_name=self.label_set_name
        )["customGroup"]

    def _get_taxonomy_segmentation(self) -> Any:
        if self.customGroup["taskType"] in self.valid_task_types:
            return self._create_taxonomy_segmentation()
        return None

    def _create_taxonomy_segmentation(self):
        tax_map: Dict[str, int] = {}
        self._trav_tax(self.taxonomy["categories"][0], tax_map)
        return self._taxonomy_update_segmentation(tax_map)

    def _trav_tax(self, taxonomy: Dict[Any, Any], tax_map: Dict[str, int]) -> None:
        """Traverse the taxonomy tree structure, and fill the taxonomy mapper object."""
        children = taxonomy["children"]
        if len(children) == 0:
            return

        for child in children:
            tax_map[child["name"]] = child["classId"]
            self._trav_tax(child, tax_map)

    def _taxonomy_update_segmentation(self, tax_map: Dict[str, int]) -> Dict[str, int]:
        """
        Fix the taxonomy mapper object to be 1-indexed for
        segmentation projects.
        """
        for key in tax_map.keys():
            tax_map[key] += 1
            if tax_map[key] == 0:
                print_error(
                    "Taxonomy class id's must be 0 indexed. \
                        Please contact contact@redbrickai.com for help."
                )
                exit(1)

        # Add a background class for segmentation
        tax_map["background"] = 0
        return tax_map

    def _trim_labels(self, entry) -> Dict:
        """Trims None values from labels"""
        for label in entry["labelData"]["labels"]:
            for k, v in label.copy().items():
                if v is None:
                    del label[k]
        return entry

    def __iter__(self) -> Iterable[Dict]:
        return self

    def __next__(self) -> dict:
        """Get next labels / datapoint."""

        # If cursor is None and current datapointsBatch has been processed
        if (
            self.datapointsBatchIndex is not None
            and self.cursor is None
            and len(self.datapointsBatch) == self.datapointsBatchIndex
        ):
            raise StopIteration

        # If current datapointsBatch is None or we have finished processing current datapointsBatch
        if (
            self.datapointsBatch is None
            or len(self.datapointsBatch) == self.datapointsBatchIndex
        ):
            if self.cursor is None:
                customGroup = self.api.get_datapoints_paged(
                    org_id=self.org_id, label_set_name=self.label_set_name
                )
            else:
                customGroup = self.api.get_datapoints_paged(
                    org_id=self.org_id,
                    label_set_name=self.label_set_name,
                    cursor=self.cursor,
                )
            self.cursor = customGroup["customGroup"]["datapointsPaged"]["cursor"]
            self.datapointsBatch = customGroup["customGroup"]["datapointsPaged"][
                "entries"
            ]
            self.datapointsBatchIndex = 0

        # Current entry to return
        entry = self.datapointsBatch[self.datapointsBatchIndex]
        self.datapointsBatchIndex += 1

        return self._trim_labels(entry)
