"""
Testing the segmentation module.
"""

from redbrick.entity.label import ImageSegmentation
from redbrick.entity.label.segmentation import ImageSegmentationRemoteLabel
import matplotlib.pyplot as plt

# d8888b.  .d8b.  d888888b  .d8b.
# 88  `8D d8' `8b `~~88~~' d8' `8b
# 88   88 88ooo88    88    88ooo88
# 88   88 88~~~88    88    88~~~88
# 88  .8D 88   88    88    88   88
# Y8888D' YP   YP    YP    YP   YP

remote_label1 = [
    {
        "category": [["object", "car"]],
        "attributes": [],
        "pixel": {"imagesize": [100, 100], "regions": [], "holes": [],},
        "labelid": "123",
    }
]

classes1 = {"car": 1, "person": 2}

remote_label2 = [
    {
        "category": [["object", "car"]],
        "attributes": [],
        "pixel": {
            "imagesize": [100, 100],
            "regions": [[[0, 0], [10, 0], [10, 10], [0, 10]]],
            "holes": [],
        },
        "labelid": "123",
    }
]

remote_label3 = [
    {
        "category": [["object", "car"]],
        "attributes": [],
        "pixel": {
            "imagesize": [100, 100],
            "regions": [[[0, 0], [10, 0], [10, 10], [0, 10]]],
            "holes": [],
        },
        "labelid": "123",
    },
    {
        "category": [["object", "person"]],
        "attributes": [],
        "pixel": {
            "imagesize": [100, 100],
            "regions": [[[9, 0], [19, 0], [19, 10], [9, 10]]],
            "holes": [],
        },
        "labelid": "123",
    },
]

remote_label4 = [
    {
        "category": [["object", "car"]],
        "attributes": [],
        "pixel": {
            "imagesize": [100, 100],
            "regions": [[[0, 0], [10, 0], [10, 10], [0, 10]]],
            "holes": [[[3, 3], [11, 3], [11, 11], [3, 11]]],
        },
        "labelid": "123",
    }
]

remote_label5 = [
    {
        "category": [["object", "person"]],
        "attributes": [],
        "pixel": {
            "imagesize": [100, 100],
            "regions": [[[14, 14], [16, 14], [16, 16], [14, 16]]],
            "holes": [],
        },
        "labelid": "123",
    },
    {
        "category": [["object", "car"]],
        "attributes": [],
        "pixel": {
            "imagesize": [100, 100],
            "regions": [[[10, 10], [20, 10], [20, 20], [10, 20]]],
            "holes": [[[12, 12], [18, 12], [18, 18], [12, 18]]],
        },
        "labelid": "123",
    },
]

# d888888b d88888b .d8888. d888888b .d8888.
# `~~88~~' 88'     88'  YP `~~88~~' 88'  YP
#    88    88ooooo `8bo.      88    `8bo.
#    88    88~~~~~   `Y8b.    88      `Y8b.
#    88    88.     db   8D    88    db   8D
#    YP    Y88888P `8888Y'    YP    `8888Y'


def test_init_empty() -> None:
    """Test basic initialization."""
    # arrange
    remote_label_1 = [
        ImageSegmentationRemoteLabel.from_dict(label) for label in remote_label1
    ]

    # action
    image_segment = ImageSegmentation(classes=classes1, remote_labels=remote_label_1)

    # assert
    assert image_segment.mask.shape == (100, 100)
    assert (image_segment.mask == 0).all()


def test_init_basic() -> None:
    """Test basic non empty initialization."""
    # arrange
    remote_label_2 = [
        ImageSegmentationRemoteLabel.from_dict(label) for label in remote_label2
    ]

    # action
    image_segment = ImageSegmentation(classes=classes1, remote_labels=remote_label_2)

    # assert
    assert (image_segment.mask[0:10, 0:10] == 1).all()
    assert (image_segment.mask[10:100, 10:100] == 0).all()


def test_init_two_obj() -> None:
    """Test basic init for multiple overlapping object."""
    # arrange
    remote_label_3 = [
        ImageSegmentationRemoteLabel.from_dict(label) for label in remote_label3
    ]

    # action
    image_segment = ImageSegmentation(classes=classes1, remote_labels=remote_label_3)

    # assert
    assert (image_segment.mask[0:9, 0:9] == 1).all()
    assert (image_segment.mask[0:9, 9:19] == 2).all()


def test_init_single_hole() -> None:
    """
    Test basic init for single hole single region. 
    This hole "spills outside" the region.
    """
    # arrange
    remote_label_4 = [
        ImageSegmentationRemoteLabel.from_dict(label) for label in remote_label4
    ]

    # action
    image_segment = ImageSegmentation(classes=classes1, remote_labels=remote_label_4)

    # assert
    assert (image_segment.mask[3:11, 3:11] == 0).all()


def test_init_reg_inside_hole() -> None:
    """Test a region inside another region's hole."""
    # arrange
    remote_label_5 = [
        ImageSegmentationRemoteLabel.from_dict(label) for label in remote_label5
    ]

    # action
    image_segment = ImageSegmentation(classes=classes1, remote_labels=remote_label_5)

    # assert
    assert (image_segment.mask[14:16, 14:16] == 2).all()  # inner region
    assert (image_segment.mask[12:14, 12:18] == 0).all()  # inner hole
    assert (image_segment.mask[12:18, 12:14] == 0).all()  # inner hole
    assert (image_segment.mask[12:18, 16:18] == 0).all()  # inner hole
    assert (image_segment.mask[16:18, 12:18] == 0).all()  # inner hole
    assert (image_segment.mask[10:12, 10:20] == 1).all()  # outer region
    assert (image_segment.mask[18:20, 10:20] == 1).all()  # outer region
    assert (image_segment.mask[10:20, 10:12] == 1).all()  # outer region
    assert (image_segment.mask[10:20, 18:20] == 1).all()  # outer region

