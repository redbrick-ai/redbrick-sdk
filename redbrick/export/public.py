"""Public API to exporting."""

import tqdm  # type: ignore
from typing import List, Dict, Callable, Optional, Tuple
from functools import partial
from redbrick.common.context import RBContext
from redbrick.utils.pagination import PaginationIterator
from redbrick.utils.rb_label_utils import clean_rb_label, flat_rb_format
from redbrick.coco.coco_main import coco_converter


class Export:
    """Primary interface to handling export from a project."""

    def __init__(self, context: RBContext, org_id: str, project_id: str) -> None:
        """Construct Export object."""
        self.context = context
        self.org_id = org_id
        self.project_id = project_id

    def _get_raw_data(self, only_ground_truth: bool = True) -> Tuple[List[Dict], Dict]:
        temp = self.context.export.get_datapoints_output
        if not only_ground_truth:
            raise NotImplementedError()

        my_iter = PaginationIterator(
            partial(temp, self.org_id, self.project_id, 50, True)
        )

        general_info = self.context.export.get_output_info(self.org_id, self.project_id)

        def _parse_entry(item: Dict) -> Dict:
            items_presigned = item["itemsPresigned"]
            items = item["items"]
            name = item["name"]
            dp_id = item["dpId"]
            created_by = item["labelData"]["createdByEmail"]
            labels = [clean_rb_label(label) for label in item["labelData"]["labels"]]

            return flat_rb_format(
                labels, items, items_presigned, name, dp_id, created_by
            )

        print("Downloading datapoints")
        return (
            [
                _parse_entry(val)
                for val in tqdm.tqdm(
                    my_iter, unit=" datapoints", total=general_info["datapointCount"]
                )
            ],
            general_info["taxonomy"],
        )

    def redbrick_format(self, only_ground_truth: bool = True,) -> List[Dict]:
        """Export data into redbrick format."""
        datapoints, taxonomy = self._get_raw_data(only_ground_truth)
        return datapoints

    def coco_format(self, only_ground_truth: bool = True) -> Dict:
        """Export project into coco format."""
        datapoints, taxonomy = self._get_raw_data(only_ground_truth)

        return coco_converter(datapoints, taxonomy)
