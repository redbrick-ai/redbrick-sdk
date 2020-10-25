"""
Test the bounding box module.
"""
from redbrick.entity.label import ImageBoundingBox, VideoBoundingBox
from redbrick.entity.taxonomy2 import Taxonomy2
from redbrick.tests.taxonomy2_test import TAXONOMY2, TAXONOMY1
import json

#  ____    _  _____  _
# |  _ \  / \|_   _|/ \
# | | | |/ _ \ | | / _ \
# | |_| / ___ \| |/ ___ \
# |____/_/   \_\_/_/   \_\

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


# __     _____ ____  _____ ___    ____    _  _____  _
# \ \   / /_ _|  _ \| ____/ _ \  |  _ \  / \|_   _|/ \
#  \ \ / / | || | | |  _|| | | | | | | |/ _ \ | | / _ \
#   \ V /  | || |_| | |__| |_| | | |_| / ___ \| |/ ___ \
#    \_/  |___|____/|_____\___/  |____/_/   \_\_/_/   \_\

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
