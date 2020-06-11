# Introduction

This is an SDK to make integrating with the RedBrick platform as easy as possible. This includes uploading and downloading data
as well as making your datasets easily available for training. Use this SDK to access your data and labls anywhere you run your code. Whether that is on the cloud, or locally with a Jupyter Notebook.

This repository is far from feature complete and is under active development. Please feel free to submit issues on github or at <mailto:support@redbrickai.com> if you run into any problems or have suggestions.

## Quickstart

After creating an account on app.redbrickai.com,

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

# load all images and labels into memory
all_images = []
for ii in range(label_set.number_of_datapoints()):
    item = label_set.get_item(ii)
    all_images.append(item)

label_set.show_image(all_images[0])

```

## PyTorch
A basic implementation of a PyTorch Dataset object is given below.

This Dataset can be used with the PyTorch DataLoader to perform batching and multithreading.

This example also demonstrates the redbrick.labelset.training function which creates LabelsetLoaders
for train and test data.
```python
"""redbrick-sdk quickstart, PyTorch Dataset."""
import redbrick
from redbrick.torch.transforms import (
    DetectoFormat,
    MinMaxBoxes,
    UnnormalizeBoxes,
    RedbrickToTensor,
)
from redbrick.torch import RedbrickTorchDataset
from torchvision.transforms import Compose
from torch.utils.data import DataLoader

redbrick.init(api_key="YOUR_API_KEY_HERE")

train_set, test_set = redbrick.labelset.training(
    org_id="ORG_ID_HERE",
    label_set_name="NAME",
    test_split=0.1,  # 10% of data will be held back for testing
)
transforms = Compose(
    [
        MinMaxBoxes(),  # [x1, y1, w, h] -> [x1, y1, x2, y2]
        UnnormalizeBoxes(),  # Convert box points from [0,1] -> [0, image size]
        RedbrickToTensor(),  # Convert image from np.ndarray to torch.tensor
        DetectoFormat(),  # tuple(image, {"boxes": boxes, "labels": labels})
    ]
)

train_dataset = RedbrickTorchDataset(train_set, transforms=transforms)
test_dataset = RedbrickTorchDataset(test_set, transforms=transforms)

training_data_loader = DataLoader(
    train_dataset, shuffle=True, batch_size=20, num_workers=20
)

```


## Developing

```bash
pip install -e .[dev]
```