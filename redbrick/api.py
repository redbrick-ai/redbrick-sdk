"""Getting data from redbrick api."""

import redbrick
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional
import requests
import numpy as np  # type: ignore
import cv2  # type: ignore
from .api_base import RedBrickApiBase
from .entity import DataPoint, BoundingBox


class RedBrickApi(RedBrickApiBase):
    """Implement Abstract API."""

    def __init__(self, cache: bool = False, custom_url: Optional[str] = None) -> None:
        """Construct RedBrickApi."""
        self.cache: Dict[str, Dict[str, Dict[str, DataPoint]]] = {}
        self.client = redbrick.client.RedBrickClient()
        if custom_url:
            self.url = custom_url
        else:
            self.url = "https://redbrick-backend.herokuapp.com/graphql/"

    def get_datapoint_ids(self, org_id: str, label_set_name: str) -> List[str]:
        """Get a list of datapoint ids in labelset."""
        query_string = """
            query ($orgId:UUID!, $name:String!) {
                customGroup(orgId: $orgId, name: $name) {
                    datapoints(skip:0, first:-1) {
                        dpId
                    }
                }
            }
        """

        query_variables = {"orgId": org_id, "name": label_set_name}
        query = dict(query=query_string, variables=query_variables)

        result = self._execute_query(query)

        all_dp_ids = [dp["dpId"] for dp in result["customGroup"]["datapoints"]]
        return all_dp_ids

    def get_datapoint(self, org_id: str, label_set_name: str, dp_id: str) -> DataPoint:
        """Get all relevant information related to a datapoint."""
        temp = self.cache.get(org_id, {}).get(label_set_name, {}).get(dp_id)
        if temp:
            return temp

        query_string = """
            query ($orgId: UUID!, $dpId: UUID!, $name:String!) {
                labelData(orgId: $orgId, dpId: $dpId, customGroupName: $name) {
                    blob
                    dataPoint {
                        items(presigned:true)
                    }
                }
            }
        """
        query_variables = {"orgId": org_id, "name": label_set_name, "dpId": dp_id}
        query = dict(query=query_string, variables=query_variables)
        result = self._execute_query(query)
        # parse result
        image_url = result["labelData"]["dataPoint"]["items"][0]
        labels = json.loads(result["labelData"]["blob"])["items"][0]["labels"]

        # get image array
        image = self._url_to_image(image_url)

        dpoint = DataPoint(org_id, label_set_name, dp_id, image)
        # convert labels and initialize ground truth
        dpoint.gt_boxes = [BoundingBox.from_remote(label["bbox2d"]) for label in labels]
        dpoint.gt_boxes_classes = [label["category"][0][0] for label in labels]

        self.cache[org_id] = self.cache.get(org_id, {})
        self.cache[org_id][label_set_name] = self.cache[org_id].get(label_set_name, {})
        self.cache[org_id][label_set_name][dp_id] = dpoint

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


# @dataclass
# class GraphQLQuery:
#     """Query to execute on GraphQL."""

#     query: str
#     variables: Dict


# @dataclass
# class DataPoint:
#     """A Datapoint returned by GraphQL query."""

#     image_url: str
#     labels: str


# def get_datapoint_ids(org_id: str, label_set_name: str) -> List[str]:
#     """Get all data points in the label set."""


# def get_datapoint(org_id: str, label_set_name: str, dp_id: str) -> DataPoint:
#     """Get data needed for a specific data point."""
#     query_string = """
#         query ($orgId: UUID!, $dpId: UUID!, $name:String!) {
#             labelData(orgId: $orgId, dpId: $dpId, customGroupName: $name) {
#                 blob
#                 dataPoint {
#                     items(presigned:true)
#                 }
#             }
#         }
#     """
#     query_variables = {"orgId": org_id, "name": label_set_name, "dpId": dp_id}
#     query = GraphQLQuery(query_string, query_variables)
#     result = execute_query(query)
#     return DataPoint(
#         labels=result["labelData"]["blob"],
#         image_url=result["labelData"]["dataPoint"]["items"][0],
#     )
