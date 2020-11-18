"""
Utility functions.
"""

from typing import List
import requests
import numpy as np  # type: ignore
import cv2  # type: ignore
from redbrick.entity.taxonomy2 import Taxonomy2


def url_to_image(url: str) -> np.ndarray:
    """Get image data from url."""
    # Download the image, convert it to a NumPy array, and then read
    # it into OpenCV format

    resp = None

    try:
        resp = requests.get(url, stream=True)
        resp.raw.decode_content = True

        # check for errors
        if not resp.status_code == 200:
            raise Exception("Not able to access data at %s url" % (url))
    except Exception as err:
        raise Exception(
            "%s. Not able to access data at %s url" % (str(err), url)
        ) from err

    image = np.asarray(bytearray(resp.raw.read()), dtype="uint8")
    # pylint: disable=no-member
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)

    # cv2 returns a BGR image, need to convert to RGB
    # the copy operation makes the memory contiguous for tensorify-ing
    return np.flip(image, axis=2).copy()


def compare_taxonomy(category_path: List[List[str]], taxonomy: Taxonomy2) -> bool:
    """Check if the category_path is valid for taxonomy."""
    tax_obj = taxonomy.taxonomy["categories"]

    for idx, cat in enumerate(category_path[0]):
        # Iterate through the tax obj
        for elem in tax_obj:
            if cat == elem["name"]:
                tax_obj = elem["children"]

                # Make sure this is the last category in path, and last elem in tax tree
                if len(tax_obj) == 0 and idx == len(category_path[0]) - 1:
                    return True

    return False
