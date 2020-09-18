"""Running inference on input images."""

import torchvision
from redbrick.coco_classes import COCO_INSTANCE_CATEGORY_NAMES


def get_prediction(img, threshold):
    """Get bounding box predictions on image."""
    model = torchvision.models.detection.fasterrcnn_resnet50_fpn(pretrained=True)
    model.eval()
    transform = torchvision.transforms.Compose(
        [torchvision.transforms.ToTensor()]
    )  # Defing PyTorch Transform
    img = transform(img)  # Apply the transform to the image
    pred = model([img])  # Pass the image to the model
    print(pred)
    pred_class = [
        COCO_INSTANCE_CATEGORY_NAMES[i] for i in list(pred[0]["labels"].numpy())
    ]  # Get the Prediction Score
    pred_boxes = [
        [(i[0], i[1]), (i[2], i[3])] for i in list(pred[0]["boxes"].detach().numpy())
    ]  # Bounding boxes
    pred_score = list(pred[0]["scores"].detach().numpy())
    pred_t = [pred_score.index(x) for x in pred_score if x > threshold][
        -1
    ]  # Get list of index with score greater than threshold.
    pred_boxes = pred_boxes[: pred_t + 1]
    pred_class = pred_class[: pred_t + 1]
    return pred_boxes, pred_class
