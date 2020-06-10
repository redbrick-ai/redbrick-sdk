"""Utilities for training with RedBrick labelsets."""
import random
from typing import Tuple
import redbrick
from .loader import LabelsetLoader


def training(
    org_id: str, label_set_name: str, test_split: float, validation_split: float = 0.0
) -> Tuple[LabelsetLoader, LabelsetLoader]:
    """Create a training split and give 2 loaders."""
    if test_split < 0 or test_split > 1:
        raise Exception("value of `test_split` must be in range [0, 1]")
    dp_ids = redbrick.api.get_datapoint_ids(org_id, label_set_name)

    random.shuffle(dp_ids)

    cut_off = int((1 - test_split) * len(dp_ids))

    train = LabelsetLoader(org_id, label_set_name, dp_ids=dp_ids[:cut_off])
    test = LabelsetLoader(org_id, label_set_name, dp_ids=dp_ids[cut_off:])

    return train, test
