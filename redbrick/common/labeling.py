"""Abstract interface to exporting."""

from typing import Optional, List, Dict, Sequence, Tuple
from abc import ABC, abstractmethod
import aiohttp

from redbrick.common.storage import StorageMethod
from redbrick.types.task import OutputTask, Comment


class LabelingRepo(ABC):
    """Abstract interface to Labeling APIs."""

    @abstractmethod
    async def presign_labels_path(
        self,
        session: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        task_id: str,
        version_id: str,
        data_count: int,
        seg_count: int,
    ) -> Tuple[List[Dict], List[Dict]]:
        """Presign labels path."""

    @abstractmethod
    async def put_labeling_results(
        self,
        session: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        stage_name: str,
        task_id: str,
        labels_data: Optional[str] = None,
        labels_data_path: Optional[str] = None,
        labels_map: Optional[Sequence[Optional[Dict]]] = None,
        finished: bool = True,
    ) -> None:
        """Put Labeling results."""

    @abstractmethod
    async def put_labeling_task_result(
        self,
        session: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        stage_name: str,
        task_id: str,
    ) -> None:
        """Put labeling result for task."""

    @abstractmethod
    async def put_review_task_result(
        self,
        session: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        stage_name: str,
        task_id: str,
        review_val: bool,
        review_comment: Optional[Comment] = None,
    ) -> None:
        """Put review result for task."""

    @abstractmethod
    def assign_tasks(
        self,
        org_id: str,
        project_id: str,
        task_ids: List[str],
        emails: Optional[List[str]] = None,
        current_user: bool = False,
        refresh: bool = True,
    ) -> List[Dict]:
        """Assign tasks to specified email or current API key."""

    @abstractmethod
    async def move_task_to_start(
        self,
        session: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        task_id: str,
    ) -> None:
        """Move groundtruth task back to start."""

    @abstractmethod
    def update_model_tasks_state(
        self,
        org_id: str,
        project_id: str,
        task_ids: List[str],
        action: str,
    ) -> None:
        """Update model tasks state."""


class Labeling(ABC):
    """
    Perform programmatic labeling and review tasks.

    The Labeling class allows you to programmatically submit tasks.
    This can be useful for times when you want to make bulk actions
    e.g accepting several tasks, or make automated actions like using automated
    methods for review.

    .. admonition:: Information

      The Labeling module provides several methods to query tasks and assign tasks to
      different users. Refer to this section for guidance on when to use each method:

      - :obj:`assign_tasks`.
        Use this method when you already have
        the ``task_ids`` you want to assign to a particular user. If you don't have the
        ``task_ids``, you can query the tasks using :obj:`~redbrick.common.export.Export.list_tasks`.
    """

    @abstractmethod
    def put_tasks(
        self,
        stage_name: str,
        tasks: List[OutputTask],
        *,
        finalize: bool = True,
        existing_labels: bool = False,
        rt_struct: bool = False,
        dicom_seg: bool = False,
        mhd: bool = False,
        review_result: Optional[bool] = None,
        review_comment: Optional[Comment] = None,
        label_storage_id: Optional[str] = StorageMethod.REDBRICK,
        label_validate: bool = False,
        prune_segmentations: bool = False,
        concurrency: int = 50,
    ) -> List[OutputTask]:
        """
        Put tasks with new labels or a review result.

        Use this method to programmatically submit tasks with labels in `Label stage`, or to
        programmatically accept/reject/correct tasks in a `Review stage`. If you don't already
        have a list of ``task_id``, you can use :obj:`~redbrick.common.export.Export.list_tasks` to
        get a filtered list of tasks in your project, that you want to work upon.

        .. tab:: Label

            .. code:: python

                project = redbrick.get_project(...)
                tasks = [
                    {
                        "taskId": "...",
                        "series": [{...}]
                    },
                ]

                # Submit tasks with new labels
                project.labeling.put_tasks("Label", tasks)

                # Save tasks with new labels, without submitting
                project.labeling.put_tasks("Label", tasks, finalize=False)

                # Submit tasks with existing labels
                project.labeling.put_tasks("Label", [{"taskId":"..."}], existing_labels=True)


        .. tab:: Review

            .. code:: python

                project = redbrick.get_project(...)

                # Set review_result to True if you want to accept the tasks
                project.review.put_tasks("Review_1", [{taskId: "..."}], review_result=True)

                # Set review_result to False if you want to reject the tasks
                project.review.put_tasks("Review_1", [{taskId: "..."}], review_result=False)

                # Add labels if you want to accept the tasks with correction
                project.review.put_tasks("Review_1", [{taskId: "...", series: [{...}]}])


        Parameters
        --------------
        stage_name: str
            The stage to which you want to submit the tasks. This must be the
            same stage as which you called get_tasks on.

        tasks: List[:obj:`~redbrick.types.task.OutputTask`]
            Tasks with new labels or review result.

        finalize: bool = True
            Finalize the task. If you want to save the task without submitting, set this to False.

        existing_labels: bool = False
            If True, the tasks will be submitted with their existing labels.
            Applies only to Label stage.

        rt_struct: bool = False
            Upload segmentations from DICOM RT-Struct files.

        dicom_seg: bool = False
            Upload segmentations from DICOM Segmentation files.

        mhd: bool = False
            Upload segmentations from MHD files.

        review_result: Optional[bool] = None
            Accepts or rejects the task based on the boolean value.
            Applies only to Review stage.

        review_comment: Optional[:obj:`~redbrick.types.task.Comment`] = None
            Comment for the review result.
            Applies only to Review stage.

        label_storage_id: Optional[str] = None
            Optional label storage id to reference external nifti segmentations.
            Defaults to project settings' annotation storage_id if not specified.

        label_validate: bool = False
            Validate label nifti instances and segment map.

        prune_segmentations: bool = False
            Prune segmentations that are not part of the series.

        concurrency: int = 50

        Returns
        ---------------
        List[:obj:`~redbrick.types.task.OutputTask`]
            A list of tasks that failed.
        """

    @abstractmethod
    def assign_tasks(
        self,
        task_ids: List[str],
        *,
        email: Optional[str] = None,
        emails: Optional[List[str]] = None,
        refresh: bool = True,
    ) -> List[Dict]:
        """
        Assign tasks to specified email or current API key.

        Unassigns all users from the task if neither of the ``email`` or ``current_user`` are set.

        >>> project = redbrick.get_project(org_id, project_id, api_key)
        >>> project.labeling.assign_tasks([task_id], email=email)

        Parameters
        ------------------
        task_ids: List[str]
            List of unique ``task_id`` of the tasks you want to assign.

        email: Optional[str] = None
            The email of the user you want to assign this task to. Make sure the
            user has adequate permissions to be assigned this task in the project.

        emails: Optional[List[str]] = None
            Used for projects with Consensus activated.
            The emails of the users you want to assign this task to. Make sure the
            users have adequate permissions to be assigned this task in the project.

        refresh: bool = True
            Used for projects with Consensus activated.
            If `True`, will `overwrite` the assignment to the current users.

        Returns
        ---------------
        List[Dict]
            List of affected tasks.
                >>> [{"taskId", "name", "stageName"}]
        """

    @abstractmethod
    def move_tasks_to_start(self, task_ids: List[str]) -> None:
        """Move groundtruth tasks back to start."""
