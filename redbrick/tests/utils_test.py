"""
Test the utils functions.
"""

from redbrick.utils import compare_taxonomy
from redbrick.tests.taxonomy2_test import TAXONOMY1, TAXONOMY2
from redbrick.entity.taxonomy2 import Taxonomy2


def test_compare() -> None:
    """Test category path with simple taxonomy."""
    Taxonomy1 = Taxonomy2(remote_tax=TAXONOMY1["taxonomy"])

    cat_path = [["object", "car"]]
    assert compare_taxonomy(cat_path, Taxonomy1)

    cat_path2 = [["object", "not correct"]]
    assert not compare_taxonomy(cat_path2, Taxonomy1)

    cat_path3 = [["not correct", "car"]]
    assert not compare_taxonomy(cat_path3, Taxonomy1)

    cat_path4 = [["object"]]
    assert not compare_taxonomy(cat_path4, Taxonomy1)

    cat_path5 = [["object", "car", "not correct"]]
    assert not compare_taxonomy(cat_path5, Taxonomy1)
