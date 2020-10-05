"""A higher level abstraction."""

from typing import Optional, List
from random import randint
import datumaro

import numpy as np  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
from matplotlib import patches
import os
import datetime
from tqdm import tqdm
import logging
from termcolor import colored
import json
import cv2

from redbrick.api import RedBrickApi
from redbrick.entity import DataPoint
from redbrick.entity import Datum


class LabelsetLoader:
    """A basic high level loader class."""

    def __init__(
        self, org_id: str, label_set_name: str, dp_ids: Optional[List[str]] = None
    ) -> None:
        """Construct Loader."""
        self.org_id = org_id
        self.label_set_name = label_set_name
        self.api_client = RedBrickApi(cache=False)

        print(colored("[INFO]:", "blue"), "Counting available datapoints...")
        if dp_ids:
            # Labelset with user defined datapoint id's
            self.dp_ids = dp_ids
            custom_group = self.api_client.get_custom_group(
                self.org_id, self.label_set_name
            )
            self.task_type = custom_group.task_type
            self.data_type = custom_group.data_type
            self.taxonomy = custom_group.taxonomy

        else:
            # All datapoints in labelset
            self.dp_ids, custom_group = self.api_client.get_datapoint_ids(
                self.org_id, self.label_set_name
            )
            self.task_type = custom_group.task_type
            self.data_type = custom_group.data_type
            self.taxonomy = custom_group.taxonomy
        print(
            colored("[INFO]:", "blue"), "Number of Datapoints = %s" % len(
                self.dp_ids)
        )

        # Update taxonomy mapper if segmentation
        if self.task_type == "SEGMENTATION":
            self.taxonomy_update_segmentation()

    def __getitem__(self, index: int) -> DataPoint:
        """Get information needed for a single item."""
        dp = self.api_client.get_datapoint(
            self.org_id,
            self.label_set_name,
            self.dp_ids[index],
            self.task_type,
            self.taxonomy,
        )
        return dp

    def export(self):
        """Export."""
        print(colored("[INFO]:", "blue"), "Exporting labels")

        datum = Datum('coco', labelset=self)
        datum.cache()

    def number_of_datapoints(self) -> int:
        """Get number of datapoints."""
        return len(self.dp_ids)

    def show_random_image(self) -> None:
        """Show a random image."""
        idx = randint(0, self.number_of_datapoints() - 1)
        self[idx].show_image(show_gt=True)

    def taxonomy_update_segmentation(self):
        """Fix the taxonomy mapper object to be 1-indexed for segmentation projects."""
        for key in self.taxonomy.keys():
            self.taxonomy[key] += 1
            if self.taxonomy[key] == 0:
                print(
                    colored("[ERROR]:", "red"),
                    "Taxonomy class id's must be 0 indexed. Please contact contact@redbrickai.com for help.",
                )
                exit(1)

        # Add a background class for segmentation
        self.taxonomy["background"] = 0
