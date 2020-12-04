"""A higher level abstraction."""
import random
import numpy as np  # type: ignore
import matplotlib.pyplot as plt  # type: ignore

from typing import Union, Dict
from redbrick.api import RedBrickApi
from redbrick.entity.taxonomy2 import Taxonomy2
from redbrick.entity.datapoint import Image, Video
from redbrick.export import ExportImage, ExportVideo
from redbrick.logging import print_info, print_error
from redbrick.labelset.labelset_base import LabelsetBase


class LabelsetLoader(LabelsetBase):
    """Labelset loader class."""

    def __init__(self, org_id: str, label_set_name: str) -> None:
        """Construct Loader."""
        self.org_id = org_id
        self.label_set_name = label_set_name
        self.api_client = RedBrickApi(cache=False)

        print_info("Counting available datapoint...")

        # All datapoints in labelset
        try:
            self.dp_ids, tax, custom_group = self.api_client.get_datapoint_ids(
                self.org_id, self.label_set_name
            )
        except Exception as err:
            print_error(err)
            return

        self.task_type = custom_group.get("task_type")
        self.data_type = custom_group.get("data_type")
        self.taxonomy: Taxonomy2 = tax
        print_info("Number of Datapoints = %s" % len(self.dp_ids))

        # Update taxonomy mapper if segmentation
        if self.task_type == "SEGMENTATION":
            self.taxonomy_update_segmentation()

        # Get all users
        try:
            self.users = self.api_client.get_members(self.org_id)
        except Exception as err:
            print_error(err)
            return

    def __getitem__(self, index: int) -> Union[Image, Video]:
        """Get information needed for a single item."""
        dp = self.api_client.get_datapoint(
            self.org_id,
            self.label_set_name,
            self.dp_ids[index],
            self.task_type,
            self.taxonomy.taxonomy_class_id_map,
        )
        return dp

    def export(self, format: str = "redbrick") -> str:
        """Export."""
        if self.data_type == "IMAGE":
            export_img: ExportImage = ExportImage(format=format, labelset=self)
            export_img.export()
            return export_img.cache_dir
        elif self.data_type == "VIDEO":
            export_vid: ExportVideo = ExportVideo(format=format, labelset=self)
            export_vid.export()
            return export_vid.cache_dir
        else:
            err = ValueError(
                "%s data type not supported! Please reach out to \
                    contact@redbrickai.com"
                % self.data_type
            )
            print_error(err)
            return ""

    def number_of_datapoints(self) -> int:
        """Get number of datapoints."""
        return len(self.dp_ids)

    def show_data(self) -> None:
        """Visualize the data."""

        if self.data_type == "VIDEO":
            print_info("Visualizing first 20 frames...")

            num_dps = self.number_of_datapoints()
            if not num_dps:
                return

            idx = random.randint(0, num_dps - 1)

            self[idx].show_data()
            return

        # Image data type
        print_info("Visualizing data and labels...")

        # Prepare figure
        num_dps = self.number_of_datapoints()
        cols = int(np.min([2, num_dps]))
        rows = int(np.min([2, np.ceil(num_dps / cols)]))
        fig = plt.figure()

        # Generate random index list
        list_len = np.min([rows * cols, num_dps])
        indexes = random.sample(range(0, list_len), list_len)

        # Iterate through axes
        for i, idx in enumerate(indexes):
            ax = fig.add_subplot(rows, cols, i + 1)
            self[idx].show_data(ax=ax)  # type: ignore

        plt.tight_layout()
        plt.show()

    def taxonomy_update_segmentation(self) -> None:
        """
        Fix the taxonomy mapper object to be 1-indexed for
        segmentation projects.
        """
        for key in self.taxonomy.taxonomy_class_id_map:
            self.taxonomy.taxonomy_class_id_map[key] += 1
            if self.taxonomy.taxonomy_class_id_map[key] == 0:
                print_error(
                    "Taxonomy class id's must be 0 indexed. \
                        Please contact contact@redbrickai.com for help."
                )
                exit(1)

        # Add a background class for segmentation
        self.taxonomy.taxonomy_class_id_map["background"] = 0
