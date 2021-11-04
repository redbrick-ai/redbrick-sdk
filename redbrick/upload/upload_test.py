from . import Upload
import matplotlib.pyplot as plt
import numpy as np
import json


def test_mask_to_polygon():

    # read mask, and convert to binary mask
    mask = plt.imread(
        "redbrick/upload/mask_test/88664c8f-c6f8-4d5a-918e-41d8441a4509.png"
    )

    with open("redbrick/upload/mask_test/class_map.json", "r") as file:
        class_map = json.load(file)

    dp_entry = Upload._mask_to_rbai(mask, class_map, "items123", "name123")
    print(dp_entry)
    assert False
