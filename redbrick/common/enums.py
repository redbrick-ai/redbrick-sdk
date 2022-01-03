"""Enumerations for use across SDK."""

from enum import Enum


class LabelType(Enum):
    """Allowable types for labeling projects.

    - IMAGE_CLASSIFY - Classification of images
    - IMAGE_BBOX - Bounding box detections with images
    - IMAGE_POINT - Keypoint detections with images
    - IMAGE_POLYLINE - Polyline shapes with images
    - IMAGE_POLYGON - Freeform polygon detections with images
    - IMAGE_ELLIPSE - Ellipse shapes with images
    - IMAGE_SEGMENTATION - Pixel level segmentation with images
    - IMAGE_MULTI - All available image labeling types for detection and segmentation

    - VIDEO_BBOX - Bounding box detection and object tracking with video frames
    - VIDEO_POINT - Keypoint detections and object tracking with video frames
    - VIDEO_POLYLINE - Polyline shapes and object tracking with video frames
    - VIDEO_ELLIPSE - Ellipse shapes and object tracking with video frames
    - VIDEO_CLASSIFY - Frame level Classification of video frames.
    - VIDEO_POLYGON - Freeform polygon detections and object tracking with video frames
    - VIDEO_MULTI - All available video labeling types for annotating videos with multiple shapes

    - DOCUMENT_BBOX - Annotate pdf and other documents with work detection and OCR tools

    - DICOM_SEGMENTATION - 3D pixel segmentation of DICOM series data
    """

    IMAGE_ITEMS = "IMAGE_ITEMS"
    IMAGE_CLASSIFY = "IMAGE_CLASSIFY"
    IMAGE_BBOX = "IMAGE_BBOX"
    IMAGE_POINT = "IMAGE_POINT"
    IMAGE_POLYLINE = "IMAGE_POLYLINE"
    IMAGE_POLYGON = "IMAGE_POLYGON"
    IMAGE_ELLIPSE = "IMAGE_ELLIPSE"
    IMAGE_SEGMENTATION = "IMAGE_SEGMENTATION"
    IMAGE_MULTI = "IMAGE_MULTI"

    VIDEO_ITEMS = "VIDEO_ITEMS"
    VIDEO_BBOX = "VIDEO_BBOX"
    VIDEO_POINT = "VIDEO_POINT"
    VIDEO_POLYLINE = "VIDEO_POLYLINE"
    VIDEO_ELLIPSE = "VIDEO_ELLIPSE"
    VIDEO_CLASSIFY = "VIDEO_CLASSIFY"
    VIDEO_POLYGON = "VIDEO_POLYGON"
    VIDEO_MULTI = "VIDEO_MULTI"

    DOCUMENT_BBOX = "DOCUMENT_BBOX"

    DICOM_SEGMENTATION = "DICOM_SEGMENTATION"


class StorageMethod:
    """Special case storage method Ids.

    - PUBLIC - Access files from a public cloud storage service or local storage
    - REDBRICK - Access files from the RedBrickAI servers
    """

    PUBLIC = "11111111-1111-1111-1111-111111111111"
    REDBRICK = "22222222-2222-2222-2222-222222222222"


class TaskStates(Enum):
    """Potential states of task status."""

    UNASSIGNED = "UNASSIGNED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    PROBLEM = "PROBLEM"
