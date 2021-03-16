from typing import Dict, Any, List
from redbrick.api import RedBrickApi
from redbrick.logging import print_info, print_error


class DatapointCreator:
    """Datapoint creator class."""

    def __init__(
        self,
        org_id: str,
        data_set_name: str,
        storage_id: str,
        label_set_name: str = None,
    ):
        """Construct creator"""
        super().__init__()
        self.org_id = org_id
        self.data_set_name = data_set_name
        self.storage_id = storage_id
        self.label_set_name = label_set_name
        self.api_client = RedBrickApi(cache=False)

    def create_datapoint(
        self, name: str, items: List[str], labels: List[Dict] = None
    ) -> None:
        """Create a datapoint in the backend"""

        try:
            datapoint_ = self.api_client.createDatapoint(
                org_id=self.org_id,
                items=items,
                name=name,
                data_set_name=self.data_set_name,
                storage_id=self.storage_id,
                label_set_name=self.label_set_name,
                labels=labels,
            )
        except:
            print_error(
                "Could not create datapoint. Make sure your datapoint name is not repeated."
            )
            return

        print_info(
            "Datapoint successfully created. Datapoint id: {}".format(
                datapoint_["createDatapoint"]["dpId"]
            )
        )
