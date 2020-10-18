"""A higher level abstraction."""

from typing import Optional, List, Union, Dict
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

from redbrick.labelset.labelset_base import LabelsetBase
from redbrick.api import RedBrickApi
from redbrick.entity.datapoint import Image, Video
from redbrick.entity.export import ExportImage, ExportVideo


class LabelsetLoader(LabelsetBase):
    """A basic high level loader class."""

    def __init__(self, org_id: str, label_set_name: str) -> None:
        """Construct Loader."""
        self.org_id = org_id
        self.label_set_name = label_set_name
        self.api_client = RedBrickApi(cache=False)

        print(colored("[INFO]:", "blue"), "Counting available datapoints...")
        # All datapoints in labelset
        self.dp_ids, custom_group = self.api_client.get_datapoint_ids(
            self.org_id, self.label_set_name
        )
        self.task_type = custom_group.task_type
        self.data_type = custom_group.data_type
        self.taxonomy: Dict[str, int] = custom_group.taxonomy
        print(
            colored("[INFO]:", "blue"), "Number of Datapoints = %s" % len(self.dp_ids)
        )

        # Update taxonomy mapper if segmentation
        if self.task_type == "SEGMENTATION":
            self.taxonomy_update_segmentation()

    def __getitem__(self, index: int) -> Union[Image, Video]:
        """Get information needed for a single item."""
        dp = self.api_client.get_datapoint(
            self.org_id,
            self.label_set_name,
            self.dp_ids[index],
            self.task_type,
            self.taxonomy,
        )
        return dp

    def export(self, format="redbrick"):
        """Export."""
        # datum = Datum(labelset=self, label_format=format)
        # datum.export()
        if self.data_type == "IMAGE":
            export = ExportImage(format=format, labelset=self)
            export.export()
        elif self.data_type == "VIDEO":
            export = ExportVideo(format=format, labelset=self)
            export.export()
        else:
            raise ValueError(
                "%s data type not supported! Please reach out to contact@redbrickai.com"
                % self.data_type
            )

    def number_of_datapoints(self) -> int:
        """Get number of datapoints."""
        return len(self.dp_ids)

    def show_random_image(self) -> None:
        """Show a random image."""
        if self.data_type == "VIDEO":
            print(
                colored("[WARNING]:", "yellow"),
                "show_random_image function not supported for video labelset.",
            )

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
