"""Testing the image entity."""
import numpy as np  # type: ignore

from redbrick.entity.datapoint import Image
from redbrick.entity.label import (
    ImageBoundingBox,
    ImageBoundingBoxEntry,
    ImageSegmentation,
)
from .bbox_test import LABEL1
from .segmentation_test import remote_label5
from redbrick.entity.label.segmentation import (
    ImageSegmentationRemoteLabel,
    ImageSegmentation,
)
import matplotlib.pyplot as plt

IMAGE = Image(
    org_id="123",
    label_set_name="abc",
    taxonomy={"person": 2, "car": 1},
    task_type="BBOX",
    remote_labels=LABEL1,
    dp_id="123",
    image_url="abc.png",
    image_url_not_signed="abc234.png",
    image_data=np.zeros((10, 10, 3)),
    created_by="123",
)

IMAGE_SEGMENT = Image(
    org_id="123",
    label_set_name="abc",
    taxonomy={"person": 2, "car": 1},
    task_type="SEGMENTATION",
    remote_labels=remote_label5,
    dp_id="123",
    image_url="abc.png",
    image_url_not_signed="abc234.png",
    image_data=np.zeros((100, 100, 3)),
    created_by="123",
)


def test_init_bbox() -> None:
    """Test basic init."""
    # arrange
    image = IMAGE

    # assert
    assert isinstance(image.labels, ImageBoundingBox)
    assert len(image.labels.labels) == 1
    assert isinstance(image.labels.labels[0], ImageBoundingBoxEntry)


def test_init_segmentation() -> None:
    """Test basic init of segmentation."""
    # arrange
    image = IMAGE_SEGMENT

    # assert
    assert isinstance(image.labels, ImageSegmentation)
    assert len(image.remote_labels) == 2

