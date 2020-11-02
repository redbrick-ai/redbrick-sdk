"""
Test the datapoint module.
"""

from redbrick.entity.datapoint import Image, Video
from redbrick.entity.label import ImageBoundingBox, VideoBoundingBox, VideoClassify
from .taxonomy2_test import TAXONOMY1
from .bbox_test import LABEL1, VID_LABEL1
from .classify_test import VID_CLASS_1
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
    items_list=[
        "http://127.0.0.1:8080/firstadsfsadf.png",
        "http://127.0.0.1:8080/secondasdfdasrqew.png",
        "http://127.0.0.1:8080/thirdadsfqer.png",
    ],
    dp_id="sdfalsn",
    video_name="video name",
    items_list_not_signed=[
        "http://127.0.0.1:8080/firstadsfsadf.png",
        "http://127.0.0.1:8080/secondasdfdasrqew.png",
        "http://127.0.0.1:8080/thirdadsfqer.png",
    ],
)

VIDEO_CLASSIFY = Video(
    org_id="123",
    label_set_name="abc",
    taxonomy={"person": 0, "car": 1},
    task_type="CLASSIFY",
    remote_labels=VID_CLASS_1,
    items_list=[
        "http://127.0.0.1:8080/firstadsfsadf.png",
        "http://127.0.0.1:8080/secondasdfdasrqew.png",
        "http://127.0.0.1:8080/thirdadsfqer.png",
    ],
    dp_id="sdfalsn",
    video_name="video name",
    items_list_not_signed=[
        "http://127.0.0.1:8080/firstadsfsadf.png",
        "http://127.0.0.1:8080/secondasdfdasrqew.png",
        "http://127.0.0.1:8080/thirdadsfqer.png",
    ],
)


def test_image_init() -> None:
    """test init of image."""

    image = IMAGE
    assert len(image.labels.labels) == 1
    assert isinstance(image.labels, ImageBoundingBox)


def test_video_bbox_init() -> None:
    """test init of video."""
    video = VIDEO

    assert len(video.labels.labels) == 3
    assert isinstance(video.labels, VideoBoundingBox)


def test_video_classify_init() -> None:
    """Test video classify."""
    video = VIDEO_CLASSIFY

    assert len(video.labels.labels) == 3
    assert isinstance(video.labels, VideoClassify)
