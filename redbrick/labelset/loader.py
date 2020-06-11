"""A higher level abstraction."""

from typing import Optional, List
from random import randint

import numpy as np  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
from matplotlib import patches

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
        if dp_ids:
            self.dp_ids = dp_ids
        else:
            self.dp_ids = self.api_client.get_datapoint_ids(
                self.org_id, self.label_set_name
            )
        print(len(self.dp_ids))

    def __getitem__(self, index: int) -> DataPoint:
        """Get information needed for a single item."""
        return self.api_client.get_datapoint(
            self.org_id, self.label_set_name, self.dp_ids[index]
        )

    def number_of_datapoints(self) -> int:
        """Get number of datapoints."""
        return len(self.dp_ids)

    def show_random_image(self) -> None:
        """Show a random image."""
        idx = randint(0, self.number_of_datapoints() - 1)
        self[idx].show_image(show_gt=True)
