"""
Utility functions.
"""

import requests
import numpy as np
import cv2


def url_to_image(url: str) -> np.ndarray:
    """Get image data from url."""
    # Download the image, convert it to a NumPy array, and then read
    # it into OpenCV format
    resp = requests.get(url, stream=True)
    resp.raw.decode_content = True
    image = np.asarray(bytearray(resp.raw.read()), dtype="uint8")
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    # cv2 returns a BGR image, need to convert to RGB
    # the copy operation makes the memory contiguous for tensorify-ing
    return np.flip(image, axis=2).copy()
