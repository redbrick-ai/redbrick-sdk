"""
Test the datapoint module.
"""

from redbrick.entity.datapoint import Image, Video
from redbrick.entity.label import ImageBoundingBox, VideoBoundingBox
from .taxonomy2_test import TAXONOMY1
from .bbox_test import LABEL1, VID_LABEL1
import numpy as np  # type: ignore

IMAGE = Image(
    org_id="123",
    label_set_name="abc",
    taxonomy={"person": 0, "car": 1},
    task_type="BBOX",
    remote_labels=LABEL1,
    dp_id="123",
    image_url="abc.png",
    image_url_not_signed="abc234.png",
    image_data=np.zeros((10, 10, 3)),
)

VIDEO = Video(
    org_id="123",
    label_set_name="abc",
    taxonomy={"person": 0, "car": 1},
    task_type="BBOX",
    remote_labels=VID_LABEL1,
    items_list=["firstadsfsadf.png", "secondasdfdasrqewpng", "thirdadsfqer.png"],
    dp_id="sdfalsn",
    video_name="video name",
    items_list_not_signed=["first.png", "second.png", "third.png"],
)


def test_image_init() -> None:
    """test init of image."""

    image = IMAGE
    assert len(image.labels.labels) == 1
    assert isinstance(image.labels, ImageBoundingBox)


def test_video_init() -> None:
    """test init of video."""
    video = VIDEO

    assert len(video.labels.labels) == 3
    assert isinstance(video.labels, VideoBoundingBox)
