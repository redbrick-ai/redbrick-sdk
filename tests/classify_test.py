# mypy: ignore-errors

"""
Test the classify module.
"""
from redbrick.entity.label import VideoClassify
from redbrick.entity.taxonomy2 import Taxonomy2
from .taxonomy2_test import TAXONOMY1


VID_CLASS_1 = [
    {"category": [["object", "person"]], "frameindex": 0, "frameclassify": True},
    {"category": [["object", "person"]], "frameindex": 1, "frameclassify": True},
    {"category": [["object", "car"]], "frameindex": 2, "frameclassify": True},
]

VID_CLASS_2 = [
    {"category": [["object", "wrong"]], "frameindex": 0, "frameclassify": True},
    {"category": [["object", "person"]], "frameindex": 1, "frameclassify": True},
    {"category": [["object", "car"]], "frameindex": 2, "frameclassify": True},
]


def test_video_classify_init():
    """Test video classify init."""

    video_classify = VideoClassify(remote_labels=VID_CLASS_1)
    assert len(video_classify.labels) == 3


def test_video_classify_compare_taxonomy():
    """Test compare taxonomy."""
    tax = Taxonomy2(remote_tax=TAXONOMY1["taxonomy"])
    video_classify = VideoClassify(remote_labels=VID_CLASS_1)

    check, _ = video_classify.compare_taxonomy(taxonomy=tax)
    assert check


def test_video_classify_compare_taxonomy_wrong():
    """Incorrect taxonomy."""
    tax = Taxonomy2(remote_tax=TAXONOMY1["taxonomy"])
    video_classify = VideoClassify(remote_labels=VID_CLASS_2)

    check, fail = video_classify.compare_taxonomy(taxonomy=tax)
    assert not check
    assert fail == [["object", "wrong"]]
