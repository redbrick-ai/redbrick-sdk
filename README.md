# Introduction

This is an SDK to make integration with the RedBrick platform as easy as possible. This includes uploading and downloading data
as well as making your datasets easily available for training. Use this SDK to access your data and labels anywhere you run your code, whether that is on the cloud, or locally with a Jupyter Notebook.

This repository is far from feature complete and is under active development. Please feel free to submit issues on github or at [support@redbrickai.com](mailto:support@redbrickai.com) if you run into any problems or have suggestions.

## Quickstart

After creating an account on [app.redbrickai.com](https://app.redbrick.com),

```bash
pip install --upgrade redbrick-sdk
```

You'll need to get your API key before you can utilize the SDK.

```python
"""redbrick-sdk quickstart, framework agnostic."""
import redbrick

redbrick.init(api_key="YOUR_API_KEY_HERE")

label_set = redbrick.labelset.LabelsetLoader(org_id="ORG_ID_HERE", label_set_name="NAME")

label_set.show_random_image()

# load all images and labels into memory (not recommended for large labelsets)
all_items = []
for ii in range(label_set.number_of_datapoints()):
    item = label_set[ii]
    all_items.append(item)

# Showing some properties of the items returned by label_set
example_item = all_items[-1]
example_item.show_image()
example_item.image.shape
example_item.height
example_item.width
example_item.gt
example_item.gt_classes

```

You now all the images and their labels in memory. Now you just need to plug this data in to your machine learning framework.

## Local Development

### Pre-requisite

- Python 3.8.6 (Compatible with 3.7.0 as well)

### Setup

- Create virtual environment

```
$ python3 -m venv venv
```

- Install dependencies

```
$ source venv/bin/activate
$ pip install -r requirements-dev.txt
```

## Torch

PyTorch has a Dataset class that can be subclassed. This can be used to connect the data in your RedBrick labelset
to your model for training or inference.

[https://pytorch.org/tutorials/beginner/data_loading_tutorial.html](https://pytorch.org/tutorials/beginner/data_loading_tutorial.html)

```python
from torch.utils.data import Dataset


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
        item = self.loader[idx]
        if self.transforms:
            item = self.transforms(item)
        return item

```

This dataset can then be used with a PyTorch DataLoader for batching.

Note: Proper transformations will need to be implemented in order to convert data from the redbrick-sdk DataPoint format
to whatever format your model expects.

## TensorFlow

TODO: reference implementation of `tf.data`
