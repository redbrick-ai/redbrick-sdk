"""Export to standard RedBrick format."""
from typing import Iterable, Dict
from redbrick.api import RedBrickApi
from redbrick.logging import print_info
import redbrick
from tqdm import tqdm
import os
import json

class LabelsetLabelsIterator:
    def __init__(self, org_id: str, label_set_name: str) -> None:
        """Construct LabelsetLabelsIterator."""
        self.api = RedBrickApi()
        self.label_set_name = label_set_name
        self.org_id = org_id
        self.cursor = None
        self.datapointsBatch = None
        self.datapointsBatchIndex = None
        self.datapointCount = self._get_datapoint_count()

    def _get_datapoint_count(self) -> None:
        return self.api.get_datapoints_paged(org_id = self.org_id, label_set_name = self.label_set_name)['customGroup']['datapointCount']

    def _get_batch(self) -> None:
        print(self.api.get_datapoints_paged(self.org_id, self.label_set_name))

    def _trim_labels(self, entry) -> Dict:
        """Trims None values from labels"""
        for label in entry["labelData"]["labels"]:
            for k,v in label.copy().items():
                if v is None:
                    del label[k]
        return entry

    def __iter__(self) -> Iterable[Dict]:
        return self

    def __next__(self) -> dict:
        """Get next labels / datapoint."""
        
        # If cursor is None and current datapointsBatch has been processed
        if self.datapointsBatchIndex is not None and self.cursor is None and len(self.datapointsBatch) == self.datapointsBatchIndex:
            raise StopIteration

        # If current datapointsBatch is None or we have finished processing current datapointsBatch 
        if self.datapointsBatch is None or len(self.datapointsBatch) == self.datapointsBatchIndex:
            if self.cursor is None:
                customGroup = self.api.get_datapoints_paged(org_id = self.org_id, label_set_name = self.label_set_name)
            else:
                customGroup = self.api.get_datapoints_paged(org_id = self.org_id, label_set_name = self.label_set_name, cursor = self.cursor)
            self.cursor = customGroup["customGroup"]["datapointsPaged"]["cursor"]
            self.datapointsBatch = customGroup["customGroup"]["datapointsPaged"]["entries"]
            self.datapointsBatchIndex = 0

        #Current entry to return
        entry = self.datapointsBatch[self.datapointsBatchIndex]

        self.datapointsBatchIndex += 1

        return self._trim_labels(entry)


class ExportRedbrick:
    def __init__(self, org_id: str, label_set_name: str, target_dir: str) -> None:
        """Construct ExportRedbrick."""
        self.org_id = org_id
        self.label_set_name = label_set_name
        self.target_dir = target_dir

    def export(self) -> None:
        # Create LabelsetLabelsIterator
        labelsetIter = LabelsetLabelsIterator(org_id = self.org_id, label_set_name = self.label_set_name)

        #Create target_dir if it doesn't exist
        if not os.path.exists(self.target_dir):
            os.makedirs(self.target_dir)

        print_info("Exporting datapoints to dir {}".format(self.target_dir))

        for dpoint in tqdm(labelsetIter, total=labelsetIter.datapointCount):
            dpoint_flat = {
                "dpId": dpoint["dpId"],
                "itemsPresigned":dpoint["dpId"],
                "createdByEmail":dpoint["labelData"]["createdByEmail"],
                "labels":dpoint["labelData"]["labels"]
            }

            jsonPath = os.path.join(self.target_dir, "{}.json".format(dpoint_flat["dpId"]))

            with open(jsonPath, mode="w", encoding="utf-8") as f:
                json.dump(dpoint_flat, f)
