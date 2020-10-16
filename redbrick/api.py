"""Getting data from redbrick api."""

import redbrick
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Union, Tuple
import requests
import numpy as np  # type: ignore
import cv2  # type: ignore
from .api_base import RedBrickApiBase
from .entity import DataPoint, BoundingBox, CustomGroup, VideoDatapoint
from .entity.datapoint import Image
from .entity.datapoint import Video


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

    def get_datapoint(
        self,
        org_id: str,
        label_set_name: str,
        dp_id: str,
        task_type: str,
        taxonomy: dict,
    ) -> Union[Image, Video]:
        """Get all relevant information related to a datapoint."""

        query_string = """
            query ($orgId: UUID!, $dpId: UUID!, $name:String!) {
                labelData(orgId: $orgId, dpId: $dpId, customGroupName: $name) {
                    blob
                    dataPoint {
                        items:items(presigned:true)
                        items_not_signed:items(presigned:false)
                        name
                    },
                    taskType,
                    dataType, 
                    labels {
                      category,
                      labelid, 
                      frameclassify, 
                      frameindex,
                      trackid, 
                      keyframe, 
                      end,
                      bbox2d {
                          xnorm, 
                          ynorm, 
                          wnorm, 
                          hnorm,
                      }
                    }
                }
            }
        """
        # EXECUTE THE QUERY
        query_variables = {"orgId": org_id, "name": label_set_name, "dpId": dp_id}
        query = dict(query=query_string, variables=query_variables)
        result = self._execute_query(query)

        # IMAGE DATA
        if result["labelData"]["dataType"] == "IMAGE":
            # Parse result
            signed_image_url = result["labelData"]["dataPoint"]["items"][0]
            unsigned_image_url = result["labelData"]["dataPoint"]["items_not_signed"][0]
            labels = json.loads(result["labelData"]["blob"])["items"][0]["labels"]
            image_data = self._url_to_image(signed_image_url)  # Get image array

            dpoint = Image(
                org_id=org_id,
                label_set_name=label_set_name,
                taxonomy=taxonomy,
                remote_labels=labels,
                dp_id=dp_id,
                image_url=signed_image_url,
                image_url_not_signed=unsigned_image_url,
                image_data=image_data,
                task_type=task_type,
            )
            return dpoint

        # VIDEO DATA
        else:
            # Parse the result
            items = result["labelData"]["dataPoint"]["items"]
            items_not_signed = result["labelData"]["dataPoint"]["items_not_signed"]
            labels = result["labelData"]["labels"]
            with open("result.json", "w+") as file:
                json.dump(result, file, indent=2)
            name = result["labelData"]["dataPoint"]["name"]
            dpoint_vid = Video(
                org_id=org_id,
                label_set_name=label_set_name,
                taxonomy=taxonomy,
                task_type=task_type,
                remote_labels=labels,
                dp_id=dp_id,
                video_name=name,
                items_list=items,
                items_list_not_signed=items_not_signed,
            )

            """dpoint_vid = VideoDatapoint(
                org_id, label_set_name, items, items_not_signed, task_type, labels, name
            )"""
            return dpoint_vid

    def tasksToLabelRemote(self, orgId, projectId, stageName, numTasks):
        """Get remote labeling tasks."""
        query_string = """
        query ($orgId:UUID!, $projectId:UUID!, $stageName:String!, $numTasks:Int!){
            tasksToLabelRemote(orgId:$orgId, projectId:$projectId, stageName:$stageName, numTasks:$numTasks) {
                stageName, 
                taskId,
                subName,
                modelName,
                createdAt, 
                datapoint {
                    items(presigned:false), 
                    itemsPresigned
                } 
                taskData {
                blob
                }
            }
        }
        """
        query_variables = {
            "orgId": orgId,
            "projectId": projectId,
            "stageName": stageName,
            "numTasks": numTasks,
        }
        query = dict(query=query_string, variables=query_variables)
        result = self._execute_query(query)
        return result

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
            res = {}
            if "data" in response.json():
                res = response.json()["data"]
            else:
                res = response.json()
            return res
        except ValueError:
            print(response.content)
            print(response.status_code)
