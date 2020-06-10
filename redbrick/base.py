"""Base converter to get numpy objects that represent the item."""

from dataclasses import dataclass
from typing import Dict, List
import json

import requests
import cv2  # type: ignore
import numpy as np  # type: ignore

from redbrick.api import DataPoint
from redbrick.temp_classes import LABELS


@dataclass
class BBOXImageItem:
    class_ids: np.ndarray  # (num_objects,)
    objects: np.ndarray  # (num_objects, 4)
    image: np.ndarray  # (width, height, 3)


def get_bbox_item(datum: DataPoint) -> BBOXImageItem:
    """Get a single item for training."""
    labels = json.loads(datum.labels)["items"][0]["labels"]
    categories = get_category_array(labels)
    objects = get_object_locations_array(labels)
    image_array = _url_to_image(datum.image_url)
    return BBOXImageItem(categories, objects, image_array)


def _url_to_image(url: str) -> np.ndarray:
    """Get a cv2 image object from a url."""
    # Download the image, convert it to a NumPy array, and then read
    # it into OpenCV format
    resp = requests.get(url, stream=True)
    resp.raw.decode_content = True
    image = np.asarray(bytearray(resp.raw.read()), dtype="uint8")

    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    # for some reason rgb channels are flipped
    # the copy operation makes the memory contiguous for tensorify-ing
    return np.flip(image, axis=2).copy()


def get_category_array(labels: List) -> np.ndarray:
    """
    Get an array of class ids for each object in an image.

    * array(num_objects,)
    """
    categories = [label["category"] for label in labels]

    category_index = [LABELS.index(categ[0][0]) for categ in categories]
    category_array = np.array(category_index)
    return category_array


def get_object_locations_array(labels: List) -> np.ndarray:
    """
    Get an array of object bbox locations.

    (x,y) in top left corner.

    * returns: array(num_objects, 4)

    [x_norm, y_norm, w_norm, h_norm]
    """

    def _dict_2_list(item: Dict) -> List:
        return [item["xnorm"], item["ynorm"], item["wnorm"], item["hnorm"]]

    return np.array([np.array(_dict_2_list(label["bbox2d"])) for label in labels])
