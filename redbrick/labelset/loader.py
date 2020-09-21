"""A higher level abstraction."""

from typing import Optional, List
from random import randint

import numpy as np  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
from matplotlib import patches
import os
import datetime
from tqdm import tqdm

from redbrick.api import RedBrickApi
from redbrick.entity import DataPoint


class LabelsetLoader:
    """A basic high level loader class."""

    def __init__(
        self, org_id: str, label_set_name: str, dp_ids: Optional[List[str]] = None
    ) -> None:
        """Construct Loader."""
        self.org_id = org_id
        self.label_set_name = label_set_name
        self.api_client = RedBrickApi(cache=False)

        print("Counting available data points... ", end="")
        # TODO: Get taxonomy map stuff here
        if dp_ids:
            # Labelset with user defined datapoint id's
            self.dp_ids = dp_ids
            custom_group = self.api_client.get_custom_group(
                self.org_id, self.label_set_name)
            self.task_type = custom_group.task_type
            self.data_type = custom_group.data_type
            self.taxonomy = custom_group.taxonomy

        else:
            self.dp_ids, custom_group = self.api_client.get_datapoint_ids(
                self.org_id, self.label_set_name
            )
            self.task_type = custom_group.task_type
            self.data_type = custom_group.data_type
            self.taxonomy = custom_group.taxonomy

        print(len(self.dp_ids))

    def __getitem__(self, index: int) -> DataPoint:
        """Get information needed for a single item."""
        dp = self.api_client.get_datapoint(
            self.org_id, self.label_set_name, self.dp_ids[index], self.task_type, self.taxonomy
        )
        return dp

    def export(self):
        """Export."""
        print('Exporting labels...')
        time = str(datetime.datetime.now())
        dir = 'RB_Export_%s' % time
        os.mkdir(dir)

        for i in tqdm(range(len(self.dp_ids))):
            dp = self.__getitem__(i)
            plt.imsave(dir + '/' + str(self.dp_ids[i]) + '.png', dp.gt._mask)

    def number_of_datapoints(self) -> int:
        """Get number of datapoints."""
        return len(self.dp_ids)

    def show_random_image(self) -> None:
        """Show a random image."""
        idx = randint(0, self.number_of_datapoints() - 1)
        self[idx].show_image(show_gt=True)
