"""An example of using the remote label brick."""

from dataclasses import dataclass
from typing import List
import numpy as np  # type: ignore
import random
import redbrick

redbrick.init(api_key="YOUR_API_KEY_HERE")


def mock_model(image: np.ndarray) -> List[redbrick.entity.ModelPredictedBbox]:
    """
    Your model would go here.

    This code is just generating 1 to 5 random boxes
    """
    count = random.randint(1, 5)
    generated_boxes = []
    for ii in range(count):
        temp_confidence = 0.5 * random.random() + 0.5  # [0.5, 1.0)
        temp_class_id = random.randint(0, 10)  # this depends on your taxonomy
        temp_box = 0.5 * np.random((4))  # array [0, 0.5)
        temp_prediction = redbrick.entity.ModelPredictedBbox(
            redbrick.entity.BoundingBox.from_array(temp_box),
            temp_class_id,
            temp_confidence,
        )
        generated_boxes.append(temp_prediction)
    return generated_boxes


remote_label_brick = redbrick.RemoteLabel(
    org_id="ORGID", project_id="PROJECTID", stage_name="STAGENAME"
)

print(remote_label_brick.data_type)  # IMAGE
print(remote_label_brick.task_type)  # BBOX

tasks: List[redbrick.RemoteLabelTask] = remote_label_brick.get_batch(10)

for task in tasks:
    task.generated_labels = mock_model(task.image)
