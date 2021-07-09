"""Utils for getting image size."""

from typing import Tuple
import io

import imgspy  # type: ignore
from PIL import Image  # type: ignore

import requests


def get_image_size(url: str) -> Tuple[str, int, int]:
    """Attempt to get size of image from URL."""
    with requests.get(url, stream=True) as res:
        result = imgspy.info(res.raw)

    return result["type"], result["width"], result["height"]


def url_to_image(url: str) -> Image:
    """Get image data from url."""
    data = requests.get(url).content
    return Image.open(io.BytesIO(data))
