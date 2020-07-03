"""Entities related to performing remote labeling tasks."""

from dataclasses import dataclass
from .datapoint import DataPoint


@dataclass
class ModelPredictedBbox:
    box: redbrick.entity.BoundingBox
    class_id: int
    confidence: float


@dataclass
class RemoteLabelTask:

    task_id: str
    image: np.ndarray = image
    generated_labels: Optional[List[ModelPredictedBbox]] = None
