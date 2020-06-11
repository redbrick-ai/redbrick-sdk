"""Utilities for training with RedBrick labelsets."""
import random
from typing import Tuple
import redbrick
from .loader import LabelsetLoader


def training(
    org_id: str, label_set_name: str, validation_split: float = 0.0
) -> Tuple[LabelsetLoader, LabelsetLoader]:
    """Create a training split and give 2 loaders."""
    if validation_split < 0 or validation_split > 1:
        raise Exception("value of `test_split` must be in range [0, 1]")
    dp_ids = redbrick.api.RedBrickApi().get_datapoint_ids(org_id, label_set_name)

    random.shuffle(dp_ids)

    cut_off = int((1 - validation_split) * len(dp_ids))

    train = LabelsetLoader(org_id, label_set_name, dp_ids=dp_ids[:cut_off])
    validate = LabelsetLoader(org_id, label_set_name, dp_ids=dp_ids[cut_off:])

    return train, validate
