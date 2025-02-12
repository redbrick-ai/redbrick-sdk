"""Enumerations for use across SDK."""

from enum import Enum


class TaskStates(str, Enum):
    """Task Status.

    - ``UNASSIGNED`` - The Task has not been assigned to a Project Admin or Member.
    - ``ASSIGNED`` - The Task has been assigned to a Project Admin or Member,
        but work has not begun on it.
    - ``IN_PROGRESS`` - The Task is currently being worked on by a Project Admin or Member.
    - ``COMPLETED`` - The Task has been completed successfully.
    - ``PROBLEM`` - A Project Admin or Member has raised an Issue regarding the Task,
        and work cannot continue until the Issue is resolved by a Project Admin.
    - ``SKIPPED`` - The Task has been skipped.
    - ``STAGED`` - The Task has been saved as a Draft.
    """

    UNASSIGNED = "UNASSIGNED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    PROBLEM = "PROBLEM"
    SKIPPED = "SKIPPED"
    STAGED = "STAGED"


class ReviewStates(str, Enum):
    """Task review states.

    - ``PASSED`` - The Task has been accepted in review.
    - ``FAILED`` - The Task has been rejected in review.
    - ``CORRECTED`` - The Task has been accepted with the corrections made in review.
    """

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
    NRRD3D = "NRRD3D"
    IMAGE2D = "IMAGE2D"
    VIDEO = "VIDEO"
    VIDEOFRAMES = "VIDEOFRAMES"


class TaskEventTypes(str, Enum):
    """Enumerate the different types of task events.

    - ``TASK_CREATED`` - A new task has been created.
    - ``TASK_SUBMITTED`` - A task has been submitted for review.
    - ``TASK_ACCEPTED`` - A submitted task has been accepted in review.
    - ``TASK_REJECTED`` - A submitted task has been rejected in review.
    - ``TASK_CORRECTED`` - A submitted task has been corrected in review.
    - ``TASK_ASSIGNED`` - A task has been assigned to a worker.
    - ``TASK_REASSIGNED`` - A task has been reassigned to another worker.
    - ``TASK_UNASSIGNED`` - A task has been unassigned from a worker.
    - ``TASK_SKIPPED`` - A task has been skipped by a worker.
    - ``TASK_SAVED`` - A task has been saved but not yet submitted.
    - ``GROUNDTRUTH_TASK_EDITED`` - A ground truth task has been edited.
    - ``CONSENSUS_COMPUTED`` - The consensus for a task has been computed.
    - ``COMMENT_ADDED`` - A comment has been added to a task.
    - ``CONSENSUS_TASK_EDITED`` - A consensus task has been edited.
    """

    TASK_CREATED = "TASK_CREATED"
    TASK_SUBMITTED = "TASK_SUBMITTED"
    TASK_ACCEPTED = "TASK_ACCEPTED"
    TASK_REJECTED = "TASK_REJECTED"
    TASK_CORRECTED = "TASK_CORRECTED"
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
    """Enumerate the different task filters.

    - ``ALL`` - All tasks.
    - ``GROUNDTRUTH`` - Ground truth tasks only.
    - ``UNASSIGNED`` - Tasks that have not yet been assigned to a worker.
    - ``QUEUED`` - Tasks that are queued for labeling/review.
    - ``DRAFT`` - Tasks that have been saved as draft.
    - ``SKIPPED`` - Tasks that have been skipped by a worker.
    - ``COMPLETED`` - Tasks that have been completed successfully.
    - ``FAILED`` - Tasks that have been rejected in review.
    - ``ISSUES`` - Tasks that have issues raised and cannot be completed.
    """

    ALL = "ALL"
    GROUNDTRUTH = "GROUNDTRUTH"
    UNASSIGNED = "UNASSIGNED"
    QUEUED = "QUEUED"
    DRAFT = "DRAFT"
    SKIPPED = "SKIPPED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ISSUES = "ISSUES"
