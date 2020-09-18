"""Utilities for using RedBrick data with pytorch."""

from typing import Callable, Optional, Dict

from torchvision import transforms  # type: ignore
from torch.utils.data import Dataset
from random import randint

from redbrick.labelset.loader import LabelsetLoader
from redbrick.base import BBOXImageItem


class ExampleRedbrickTorchDataset(Dataset):
    """A convenient way to train with pytorch using your data hosted on redbrick."""

    def __init__(self, rb_loader, transforms=None) -> None:
        """Construct RedbrickTorchDataset."""
        self.loader = rb_loader
        self.transforms = transforms

    def __len__(self):
        """Get the number of datapoints available."""
        return self.loader.number_of_datapoints()

    def __getitem__(self, idx):
        """Get a specific item."""
        print("Loading item from remote... ", end="")
        item = self.loader[idx]
        print("done")
        if self.transforms:
            item = self.transforms(item)
        return item
