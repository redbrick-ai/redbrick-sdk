"""
Test the bounding box module.
"""
import pytest
from redbrick.entity.label import ImageBoundingBox, VideoBoundingBox
from redbrick.entity.taxonomy2 import Taxonomy2
from redbrick.tests.taxonomy2_test import TAXONOMY2, TAXONOMY1
import json
import uuid

# d888888b .88b  d88.  .d8b.   d888b  d88888b   d8888b.  .d8b.  d888888b  .d8b.
#   `88'   88'YbdP`88 d8' `8b 88' Y8b 88'       88  `8D d8' `8b `~~88~~' d8' `8b
#    88    88  88  88 88ooo88 88      88ooooo   88   88 88ooo88    88    88ooo88
#    88    88  88  88 88~~~88 88  ooo 88~~~~~   88   88 88~~~88    88    88~~~88
#   .88.   88  88  88 88   88 88. ~8~ 88.       88  .8D 88   88    88    88   88
# Y888888P YP  YP  YP YP   YP  Y888P  Y88888P   Y8888D' YP   YP    YP    YP   YP

LABEL1 = [
    {
        "category": [["object", "car"]],
        "bbox2d": {"xnorm": 0.1, "ynorm": 0.1, "hnorm": 0.1, "wnorm": 0.1,},
    }
]

LABEL2 = [
    {
        "category": [["object", "person"]],
        "bbox2d": {"xnorm": 0.1, "ynorm": 0.1, "hnorm": 0.1, "wnorm": 0.1,},
    },
    {
        "category": [["object", "car"]],
        "bbox2d": {"xnorm": 0.1, "ynorm": 0.1, "hnorm": 0.1, "wnorm": 0.1,},
    },
]

LABEL3 = [
    {
        "category": [["object", "person"]],
        "bbox2d": {"xnorm": 0.1, "ynorm": 0.1, "hnorm": 0.1, "wnorm": 0.1,},
    },
    {
        "category": [["object", "not correct"]],
        "bbox2d": {"xnorm": 0.1, "ynorm": 0.1, "hnorm": 0.1, "wnorm": 0.1,},
    },
]


def test_init_image_bbox() -> None:
    """Test initializing."""
    image_bbox = ImageBoundingBox(labels=LABEL1)
    assert len(image_bbox.labels) == 1
    assert image_bbox.labels[0].xnorm == 0.1
    assert image_bbox.labels[0].ynorm == 0.1
    assert image_bbox.labels[0].hnorm == 0.1
    assert image_bbox.labels[0].wnorm == 0.1
    assert image_bbox.labels[0].classname == [["object", "car"]]

    image_bbox2 = ImageBoundingBox(labels=LABEL2)
    assert len(image_bbox2.labels) == 2
    assert image_bbox2.labels[0].classname == [["object", "person"]]


def test_compare_tax_image_bbox() -> None:
    """Test comparison of taxonomy."""
    taxonomy1 = Taxonomy2(remote_tax=TAXONOMY1["taxonomy"])

    image_bbox = ImageBoundingBox(labels=LABEL1)
    assert image_bbox.compare_taxonomy(taxonomy=taxonomy1)[0]

    image_bbox2 = ImageBoundingBox(labels=LABEL3)
    assert not image_bbox2.compare_taxonomy(taxonomy=taxonomy1)[0]


# db    db d888888b d8888b. d88888b  .d88b.    d8888b.  .d8b.  d888888b  .d8b.
# 88    88   `88'   88  `8D 88'     .8P  Y8.   88  `8D d8' `8b `~~88~~' d8' `8b
# Y8    8P    88    88   88 88ooooo 88    88   88   88 88ooo88    88    88ooo88
# `8b  d8'    88    88   88 88~~~~~ 88    88   88   88 88~~~88    88    88~~~88
#  `8bd8'    .88.   88  .8D 88.     `8b  d8'   88  .8D 88   88    88    88   88
#    YP    Y888888P Y8888D' Y88888P  `Y88P'    Y8888D' YP   YP    YP    YP   YP

VID_LABEL1 = [
    {
        "category": [["object", "person"]],
        "bbox2d": {"xnorm": 0.1, "ynorm": 0.1, "hnorm": 0.1, "wnorm": 0.1,},
        "frameindex": 0,
    },
    {
        "category": [["object", "car"]],
        "bbox2d": {"xnorm": 0.1, "ynorm": 0.1, "hnorm": 0.1, "wnorm": 0.1,},
        "frameindex": 0,
    },
    {
        "category": [["object", "car"]],
        "bbox2d": {"xnorm": 0.1, "ynorm": 0.1, "hnorm": 0.1, "wnorm": 0.1,},
        "frameindex": 1,
    },
]


def test_vid_bbox() -> None:
    """Test vid bbox init."""

    vid_bbox = VideoBoundingBox(labels=VID_LABEL1)

    assert len(vid_bbox.labels) == 3
    assert len(vid_bbox.labels[0].labelid) == 36
    assert vid_bbox.labels[1].keyframe


def test_vid_bbox_str() -> None:
    """Test string conversion."""

    vid_bbox = VideoBoundingBox(labels=VID_LABEL1)

    output = {
        "labels": [
            {
                "category": [["object", "person"]],
                "attributes": [],
                "bbox2d": {"xnorm": 0.1, "ynorm": 0.1, "hnorm": 0.1, "wnorm": 0.1,},
                "frameindex": 0,
                "labelid": vid_bbox.labels[0].labelid,
                "keyframe": True,
                "end": True,
                "trackid": vid_bbox.labels[0].trackid,
            },
            {
                "category": [["object", "car"]],
                "attributes": [],
                "bbox2d": {"xnorm": 0.1, "ynorm": 0.1, "hnorm": 0.1, "wnorm": 0.1,},
                "frameindex": 0,
                "labelid": vid_bbox.labels[1].labelid,
                "keyframe": True,
                "end": True,
                "trackid": vid_bbox.labels[1].trackid,
            },
            {
                "category": [["object", "car"]],
                "attributes": [],
                "bbox2d": {"xnorm": 0.1, "ynorm": 0.1, "hnorm": 0.1, "wnorm": 0.1,},
                "frameindex": 1,
                "labelid": vid_bbox.labels[2].labelid,
                "keyframe": True,
                "end": True,
                "trackid": vid_bbox.labels[2].trackid,
            },
        ],
    }

    assert json.loads(str(vid_bbox)) == output


t1 = str(uuid.uuid4())
t2 = str(uuid.uuid4())


def test_interpolate_one_frame() -> None:
    """Test interpolating only one frame."""
    # arrange
    label = {
        "category": [["object", "person"]],
        "bbox2d": {"xnorm": 0.1, "ynorm": 0.1, "hnorm": 0.1, "wnorm": 0.1,},
        "frameindex": 0,
        "trackid": t1,
        "keyframe": True,
        "end": True,
    }
    vid_bbox = VideoBoundingBox(labels=[label])
    # assume
    assert len(vid_bbox.labels) == 1

    # action
    result = vid_bbox.interpolate_labels(num_frames=1)

    # assert
    assert len(result) == 1
    assert len(result[0]) == 1
    result_label = result[0][0]
    assert result_label.xnorm == 0.1
    assert result_label.keyframe
    assert result_label.end


def test_interpolate_one_end_label_10_frames() -> None:
    # arrange
    label = {
        "category": [["object", "person"]],
        "bbox2d": {"xnorm": 0.1, "ynorm": 0.1, "hnorm": 0.1, "wnorm": 0.1,},
        "frameindex": 0,
        "trackid": t1,
        "keyframe": True,
        "end": True,
    }
    vid_bbox = VideoBoundingBox(labels=[label])
    # assume
    assert len(vid_bbox.labels) == 1

    # action
    result = vid_bbox.interpolate_labels(num_frames=10)

    # assert
    assert len(result) == 10
    assert len(result[0]) == 1
    assert len(result[1]) == 0
    result_label = result[0][0]
    assert result_label.xnorm == 0.1
    assert result_label.keyframe
    assert result_label.end


def test_interpolate_one_label_10_frames() -> None:
    # arrange
    label = {
        "category": [["object", "person"]],
        "bbox2d": {"xnorm": 0.1, "ynorm": 0.1, "hnorm": 0.1, "wnorm": 0.1,},
        "frameindex": 0,
        "trackid": t1,
        "keyframe": True,
        "end": False,
    }
    vid_bbox = VideoBoundingBox(labels=[label])
    # assume
    assert len(vid_bbox.labels) == 1, vid_bbox.labels

    # action
    result = vid_bbox.interpolate_labels(num_frames=10)

    # assert
    assert len(result) == 10
    assert len(result[0]) == 1
    result_label = result[0][0]

    assert result_label.xnorm == 0.1
    assert result_label.keyframe
    assert result_label.end == False
    last_label = result[-1][0]
    assert last_label.xnorm == 0.1
    assert last_label.end == False
    assert last_label.keyframe == False


def test_interpolate_two_labels() -> None:
    # arrange
    VID_LABEL2 = [
        {
            "category": [["object", "person"]],
            "bbox2d": {"xnorm": 0.1, "ynorm": 0.1, "hnorm": 0.1, "wnorm": 0.1,},
            "frameindex": 1,
            "trackid": t1,
            "keyframe": True,
            "end": False,
        },
        {
            "category": [["object", "person"]],
            "bbox2d": {"xnorm": 0.5, "ynorm": 0.5, "hnorm": 0.1, "wnorm": 0.5,},
            "frameindex": 3,
            "trackid": t1,
            "keyframe": True,
            "end": True,
        },
    ]
    vid_bbox = VideoBoundingBox(labels=VID_LABEL2)
    # assume
    assert len(vid_bbox.labels) == 2, vid_bbox.labels

    # acction
    result = vid_bbox.interpolate_labels(num_frames=10)

    # assert
    assert len(result) == 10
    assert len(result[0]) == 0

    assert len(result[1]) == 1
    assert result[1][0].keyframe

    assert len(result[2]) == 1
    assert not result[2][0].keyframe
    assert result[2][0].xnorm == 0.3

    assert len(result[3]) == 1
    assert result[3][0].keyframe

    assert len(result[4]) == 0
