# """Example usage of RedBrick Python SDK."""

# import redbrick

# redbrick.init(api_key="sAKEaEFkv7pzGL5MpxH3nBpbxNLzJShuq9CuM6vX5sk")

# train, test = redbrick.labelset.training(
#     org_id="5490b1b1-95d8-4ba0-9234-c915b0ea9b93",
#     label_set_name="Cars Stanford Labels",
#     test_split=0.2,
# )

# train.show_random_image()

# test.show_random_image()

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
