"""Getting data from redbrick api."""

import redbrick
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Tuple
import requests
import numpy as np  # type: ignore
import cv2  # type: ignore
from .api_base import RedBrickApiBase
from .entity import DataPoint, BoundingBox, CustomGroup


class RedBrickApi(RedBrickApiBase):
    """Implement Abstract API."""

    def __init__(self, cache: bool = False, custom_url: Optional[str] = None) -> None:
        """Construct RedBrickApi."""
        self.cache: Dict[str, Dict[str, Dict[str, DataPoint]]] = {}
        self.client = redbrick.client.RedBrickClient()
        if custom_url:
            self.url = custom_url
        elif self.client.custom_url:
            self.url = self.client.custom_url
        else:
            self.url = "https://redbrick-prod-1.herokuapp.com/graphql/"

    def get_datapoint_ids(
        self, org_id: str, label_set_name: str
    ) -> Tuple[List[str], CustomGroup]:
        """Get a list of datapoint ids in labelset."""
        query_string = """
            query ($orgId:UUID!, $name:String!) {
                customGroup(orgId: $orgId, name: $name) {
                    datapoints(skip:0, first:-1) {
                        dpId
                    }
                    taskType,
                    dataType
                    taxonomy {
                    name
                    version
                    categories {
                        name
                        children {
                        name
                        classId
                        children {
                            name
                            classId
                            children {
                            name
                            classId
                            }
                        }
                        }
                    }
                    }
                }
            }
        """
        query_variables = {"orgId": org_id, "name": label_set_name}
        query = dict(query=query_string, variables=query_variables)

        result = self._execute_query(query)

        all_dp_ids = [dp["dpId"] for dp in result["customGroup"]["datapoints"]]
        custom_group = CustomGroup(
            result["customGroup"]["taskType"],
            result["customGroup"]["dataType"],
            result["customGroup"]["taxonomy"],
        )
        return all_dp_ids, custom_group

    def get_custom_group(self, org_id: str, label_set_name: str) -> CustomGroup:
        """Get the details of a custom group object."""

        query_string = """
            query ($orgId:UUID!, $name:String!) {
                customGroup(orgId: $orgId, name: $name) {
                    taskType,
                    dataType
                }
            }
        """

        query_variables = {"orgId": org_id, "name": label_set_name}
        query = dict(query=query_string, variables=query_variables)

        result = self._execute_query(query)

        custom_group = CustomGroup(
            result["customGroup"]["taskType"], result["customGroup"]["dataType"]
        )
        return custom_group

    def get_datapoint(
        self,
        org_id: str,
        label_set_name: str,
        dp_id: str,
        task_type: str,
        taxonomy: dict,
    ) -> DataPoint:
        """Get all relevant information related to a datapoint."""
        temp = self.cache.get(org_id, {}).get(label_set_name, {}).get(dp_id)
        if temp:
            return temp

        query_string = """
            query ($orgId: UUID!, $dpId: UUID!, $name:String!) {
                labelData(orgId: $orgId, dpId: $dpId, customGroupName: $name) {
                    blob
                    dataPoint {
                        items:items(presigned:true)
                        items_not_signed:items(presigned:false)
                    },
                    taskType
                }
            }
        """
        query_variables = {"orgId": org_id, "name": label_set_name, "dpId": dp_id}
        query = dict(query=query_string, variables=query_variables)
        result = self._execute_query(query)

        # parse result
        signed_image_url = result["labelData"]["dataPoint"]["items"][0]
        unsigned_image_url = result["labelData"]["dataPoint"]["items_not_signed"][0]
        labels = json.loads(result["labelData"]["blob"])["items"][0]["labels"]

        # get image array
        image = self._url_to_image(signed_image_url)

        dpoint = DataPoint(
            org_id,
            label_set_name,
            dp_id,
            image,
            signed_image_url,
            unsigned_image_url,
            task_type,
            labels,
            taxonomy,
        )
        # convert labels and initialize ground truth
        """dpoint.gt = [BoundingBox.from_remote(
            label["bbox2d"]) for label in labels]
        dpoint.gt_classes = [label["category"][0][0] for label in labels]

        self.cache[org_id] = self.cache.get(org_id, {})
        self.cache[org_id][label_set_name] = self.cache[org_id].get(
            label_set_name, {})
        self.cache[org_id][label_set_name][dp_id] = dpoint"""

        return dpoint

    @staticmethod
    def _url_to_image(url: str) -> np.ndarray:
        """Get a cv2 image object from a url."""
        # Download the image, convert it to a NumPy array, and then read
        # it into OpenCV format
        resp = requests.get(url, stream=True)
        resp.raw.decode_content = True
        image = np.asarray(bytearray(resp.raw.read()), dtype="uint8")
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        # cv2 returns a BGR image, need to convert to RGB
        # the copy operation makes the memory contiguous for tensorify-ing
        return np.flip(image, axis=2).copy()

    def _execute_query(self, query: Dict) -> Any:
        """Execute a graphql query."""
        headers = {"ApiKey": self.client.api_key}
        try:
            response = requests.post(self.url, headers=headers, json=query)
            return response.json()["data"]
        except ValueError:
            print(response.content)
            print(response.status_code)
