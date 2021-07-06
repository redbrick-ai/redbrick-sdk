# main.py
import cv2
import numpy as np
import json
import redbrick
from redbrick.entity.label.bbox import ImageBoundingBox, ImageBoundingBoxRemoteLabel


# def load_yolo():
#     """
#     Load the YOLO model.
#     Loads the YOLO model using OpenCV, and return the net object
#     along with other important details
#     """
#     net = cv2.dnn.readNet("yolo/yolov3.weights", "yolo/yolov3.cfg")
#     classes = []
#     with open("yolo/coco.names", "r") as f:
#         classes = [line.strip() for line in f.readlines()]
#     layers_names = net.getLayerNames()
#     output_layers = [layers_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]
#     return net, classes, output_layers
def detect_objects(img, net, outputLayers):
    """Performs detection using YOLO on a single image."""
    blob = cv2.dnn.blobFromImage(
        img,
        scalefactor=0.00392,
        size=(320, 320),
        mean=(0, 0, 0),
        swapRB=True,
        crop=False,
    )
    net.setInput(blob)
    outputs = net.forward(outputLayers)
    return blob, outputs


def get_box_dimensions(outputs, height, width):
    """Parse the net prediction outputs to return bbox details."""
    boxes = []
    confs = []
    class_ids = []
    for output in outputs:
        for detect in output:
            scores = detect[5:]
            class_id = np.argmax(scores)
            conf = scores[class_id]
            if conf > 0.3:
                center_x = int(detect[0] * width)
                center_y = int(detect[1] * height)
                w = int(detect[2] * width)
                h = int(detect[3] * height)
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)
                boxes.append([x, y, w, h])
                confs.append(float(conf))
                class_ids.append(class_id)
    return boxes, confs, class_ids


def main(api_key, org_id, project_id):
    """Main function."""
    # Init redbrick-sdk
    redbrick.init(api_key=api_key, url="http://localhost:4000/graphql")
    remote_labeling = redbrick.remote_label.RemoteLabel(
        org_id=org_id, project_id=project_id, stage_name="REMOTE"
    )
    # Get task from RedBrick AI
    tasks = remote_labeling.get_task(num_tasks=1)
    # image = tasks[0].get_data(presigned_url=tasks[0].items_list_presigned[0])
    # image = np.flip(image, axis=2)  # cv2 requires BGR
    # image_height, image_width, _ = image.shape
    # cv2.resize(image, None, fx=0.4, fy=0.4)
    # Generate predictions from YOLO
    # model, classes, output_layers = load_yolo()
    # blob, outputs = detect_objects(image, model, output_layers)

    # Submit task to RedBrick AI
    labels = [
        {
            "category": [["object", "car"]],
            "bbox2d": {"xnorm": 0.1, "ynorm": 0.1, "wnorm": 0.2, "hnorm": 0.2},
            "attributes": [],
        }
    ]

    _labels = [ImageBoundingBoxRemoteLabel.from_dict(obj=l) for l in labels]
    image_bbox = ImageBoundingBox(labels=_labels)
    remote_labeling.submit_task(task=tasks[0], labels=image_bbox)


if __name__ == "__main__":
    API_KEY = "k99T6aSUtRkqeDr_yyVDvAmt5R4ZVMXePOtGXurqZ5s"
    ORG_ID = "5debf389-74ee-4165-bf5b-e689d87749e0"
    PROJECT_ID = "90df3e6f-4e88-4469-853a-8ea884c6a156"
    main(API_KEY, ORG_ID, PROJECT_ID)
