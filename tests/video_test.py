"""
Test the datapoint module.
"""

from redbrick.entity.datapoint import Image, Video
from redbrick.entity.label import ImageBoundingBox, VideoBoundingBox, VideoClassify
from .taxonomy2_test import TAXONOMY1
from .bbox_test import LABEL1, VID_LABEL1
from .classify_test import VID_CLASS_1
import numpy as np  # type: ignore
from typing import cast

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
    created_by="123",
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
    created_by="123",
)

VIDEO_BBOX_REAL = Video(
    org_id="123",
    label_set_name="abc",
    taxonomy={"person": 0, "car": 1},
    task_type="BBOX",
    remote_labels=VID_LABEL1,
    items_list=[
        "https://upload.wikimedia.org/wikipedia/commons/e/ee/Sample_abc.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/e/ee/Sample_abc.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/e/ee/Sample_abc.jpg",
    ],
    dp_id="sdfalsn",
    video_name="video name",
    items_list_not_signed=[
        "https://upload.wikimedia.org/wikipedia/commons/e/ee/Sample_abc.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/e/ee/Sample_abc.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/e/ee/Sample_abc.jpg",
    ],
    created_by="123",
)


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
