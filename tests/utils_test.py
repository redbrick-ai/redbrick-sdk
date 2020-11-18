"""
Test the utils functions.
"""
import cv2  # type: ignore
import numpy as np  # type: ignore

from redbrick.utils import compare_taxonomy
from redbrick.entity.taxonomy2 import Taxonomy2
from redbrick.utils import url_to_image

from .taxonomy2_test import TAXONOMY1


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


def test_url_to_image() -> None:
    """Test the conversion of a url to image data."""
    url = "https://upload.wikimedia.org/wikipedia/en/a/a9/Example.jpg"
    local = "tests/Example.jpg"

    # get local image
    # pylint: disable=no-member
    img_local = cv2.imread(local)
    img_local = np.flip(img_local, axis=2)

    # get remote image
    img_remote = url_to_image(url)

    comparison = img_local == img_remote

    assert comparison.all()


def test_url_to_image_invalid() -> None:
    """Test the utility function with invalid urls"""
    url = "https://not-a-real-url.jpg"
    url2 = "http://127.0.0.1:8080/not-real.jpg"

    # first image
    try:
        url_to_image(url)
        assert False
    except:
        assert True

    # second image
    try:
        url_to_image(url2)
        assert False
    except:
        assert True


if __name__ == "__main__":
    test_url_to_image_invalid()
