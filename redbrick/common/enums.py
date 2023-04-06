"""Enumerations for use across SDK."""
from enum import Enum


class StorageMethod:
    """Built-in Storage Method ID's that can be used to import data.

    - ``PUBLIC`` - Access files from a public cloud storage service or local storage.
    - ``REDBRICK`` - Access files from the RedBrickAI servers.
    """

    PUBLIC = "11111111-1111-1111-1111-111111111111"
    REDBRICK = "22222222-2222-2222-2222-222222222222"


class TaskStates(str, Enum):
    """Potential states of task status."""

    UNASSIGNED = "UNASSIGNED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    PROBLEM = "PROBLEM"
    SKIPPED = "SKIPPED"
    STAGED = "STAGED"


class ReviewStates(str, Enum):
    """Task review states."""

    PASSED = "PASSED"
    FAILED = "FAILED"
    CORRECTED = "CORRECTED"


class ImportTypes(str, Enum):
    """
    Enumerates the supported data import types.

    Please see supported data types, and file extensions
    in our `documentation here <https://docs.redbrickai.com/importing-data/direct-data-upload>`_.
    """

    DICOM3D = "DICOM3D"
    NIFTI3D = "NIFTI3D"
    IMAGE2D = "IMAGE2D"
    VIDEO = "VIDEO"
    VIDEOFRAMES = "VIDEOFRAMES"


class TaskEventTypes(str, Enum):
    """Enumerate the different types of task events."""

    TASK_CREATED = "TASK_CREATED"
    TASK_SUBMITTED = "TASK_SUBMITTED"
    TASK_ACCEPTED = "TASK_ACCEPTED"
    TASK_REJECTED = "TASK_REJECTED"
    TASK_ASSIGNED = "TASK_ASSIGNED"
    TASK_REASSIGNED = "TASK_REASSIGNED"
    TASK_UNASSIGNED = "TASK_UNASSIGNED"
    TASK_SKIPPED = "TASK_SKIPPED"
    TASK_SAVED = "TASK_SAVED"
    GROUNDTRUTH_TASK_EDITED = "GROUNDTRUTH_TASK_EDITED"
    CONSENSUS_COMPUTED = "CONSENSUS_COMPUTED"
    COMMENT_ADDED = "COMMENT_ADDED"
    CONSENSUS_TASK_EDITED = "CONSENSUS_TASK_EDITED"


class TaskFilters(str, Enum):
    """Enumerate the different task filters."""

    ALL = "ALL"
    GROUNDTRUTH = "GROUNDTRUTH"
    UNASSIGNED = "UNASSIGNED"
    QUEUED = "QUEUED"
    DRAFT = "DRAFT"
    SKIPPED = "SKIPPED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ISSUES = "ISSUES"
    BENCHMARK = "BENCHMARK"
