"""Tests for upload module."""

import matplotlib.pyplot as plt
import numpy as np
from . import Upload


def test_mask_to_polygon():
    """Test converting a mask to a polygon."""
    # read mask, and convert to binary mask
    img = plt.imread("test_mask/7b03b871-1d65-4125-a1cc-9a3e7f9df504.png")
    img = img[:, :, 0]
    img[np.where(img != 0)] = 1

    plt.imshow(img)
    # plt.show()

    polygons = list(Upload._mask_to_polygon(img))
    exterior = []
    for polygon in polygons:
        # interior = list(polygon.interiors)
        exterior += list(polygon.exterior.coords)

        # plt.plot(interior, 'ro')
    e_x = []
    e_y = []
    for point in exterior:
        e_x += [point[0]]
        e_y += [point[1]]

    plt.plot(e_x, e_y, "go")
    plt.show()

    assert False
