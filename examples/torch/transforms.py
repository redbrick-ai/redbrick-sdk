"""Custom Transforms for RedBrick data."""

from typing import Dict, Tuple
import numpy as np  # type: ignore
from redbrick.base import BBOXImageItem
import torch


class RedbrickToTensor:
    def __call__(self, item: BBOXImageItem) -> BBOXImageItem:
        """Execute."""
        item.image = ToTensor()(item.image)
        return item


class UnnormalizeBoxes:
    """Expand a bounding box based on image dimensions."""

    def __call__(self, item: BBOXImageItem) -> BBOXImageItem:
        """Execute."""
        height = item.image.shape[0]
        width = item.image.shape[1]

        item.objects[:, 0] = width * item.objects[:, 0]
        item.objects[:, 2] = width * item.objects[:, 2]
        item.objects[:, 1] = height * item.objects[:, 1]
        item.objects[:, 3] = height * item.objects[:, 3]
        return item


class MinMaxBoxes:
    """Convert bounding boxes from x, y, w, h to x1, y1, x2, y2."""

    def __call__(self, item: BBOXImageItem) -> BBOXImageItem:
        """Execute."""
        for object_ in item.objects:
            object_[2] = object_[0] + object_[2]
            object_[3] = object_[1] + object_[3]
        return item


class DetectoFormat:
    """Convert redbrick.base.BBOXImageItem to format expected by detecto."""

    def __call__(
        self, item: BBOXImageItem
    ) -> Tuple[np.ndarray, Dict[np.ndarray, np.ndarray]]:
        """Convert BBOXImageItem to format expected by detecto."""
        return (
            item.image,
            {"boxes": torch.tensor(item.objects).float(), "labels": item.class_ids},
        )
