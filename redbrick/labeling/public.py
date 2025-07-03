"""Public interface to labeling module."""

import functools
from inspect import signature
import json
import asyncio
from typing import Callable, List, Dict, Optional, Any, TypeVar, cast
from copy import deepcopy

import aiohttp

from redbrick.common.entities import RBProject
from redbrick.common.constants import DUMMY_FILE_PATH
from redbrick.common.storage import StorageMethod
from redbrick.common.labeling import Labeling
from redbrick.stage import Stage
from redbrick.stage.label import LabelStage
from redbrick.stage.review import ReviewStage
from redbrick.upload.interact import validate_json
from redbrick.utils.upload import (
    convert_mhd_to_nii_labels,
    convert_rt_struct_to_nii_labels,
    convert_dicom_seg_to_nii_labels,
    process_segmentation_upload,
)
from redbrick.utils.logging import log_error, logger
from redbrick.utils.async_utils import gather_with_concurrency, get_session
from redbrick.types.task import OutputTask, Comment


TFun = TypeVar("TFun", bound=Callable[..., Any])  # pylint: disable=invalid-name


def check_stage(func: TFun) -> TFun:
    """Check if stage exists in project and matches the interface."""

    @functools.wraps(func)
    def wrapper(
        self: "LabelingImpl", *args: Any, **kwargs: Any
    ) -> Optional[Callable[..., Any]]:
        func_args = dict(zip(list(signature(func).parameters.keys())[1:], args))
        func_args.update(kwargs)
        if func_args["stage_name"] not in [stage.stage_name for stage in self.stages]:
            log_error(
                f"Stage '{func_args['stage_name']}' does not exist in this project, "
                + f"or is not a '{'Review' if self.review else 'Label'}' stage.\n"
                + "If it exists, you may need to use the following:\n>>> "
                + f"project.{'labeling' if self.review else 'review'}.{func.__name__}(...)"
            )
            return None
        return func(self, *args, **kwargs)

    return cast(TFun, wrapper)


class LabelingImpl(Labeling):
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

    def __init__(self, project: RBProject, review: bool = False) -> None:
        """Construct Labeling."""
        self.project = project
        self.context = self.project.context
        self.review = review
        self.stages: List[Stage] = [
            stage
            for stage in self.project.stages
            if isinstance(stage, ReviewStage if review else LabelStage)
        ]

    async def _put_task(
        self,
        session: aiohttp.ClientSession,
        stage_name: str,
        task: Dict,
        finalize: bool,
        review_result: Optional[bool],
        review_comment: Optional[Comment],
        label_storage_id: str,
        project_label_storage_id: str,
        label_validate: bool,
        prune_segmentations: bool,
        existing_labels: bool,
    ) -> Optional[Dict]:
        # pylint: disable=too-many-locals
        task_id = task["taskId"]
        try:
            if self.review and review_result is not None:
                await self.context.labeling.put_review_task_result(
                    session,
                    self.project.org_id,
                    self.project.project_id,
                    stage_name,
                    task_id,
                    review_result,
                    review_comment,
                )
            elif not self.review and existing_labels:
                await self.context.labeling.put_labeling_task_result(
                    session,
                    self.project.org_id,
                    self.project.project_id,
                    stage_name,
                    task_id,
                )
            else:
                try:
                    labels_data_path, labels_map = await process_segmentation_upload(
                        self.context,
                        session,
                        self.project.org_id,
                        self.project.project_id,
                        task,
                        label_storage_id,
                        project_label_storage_id,
                        label_validate,
                        prune_segmentations,
                    )
                except ValueError as err:
                    logger.warning(
                        f"Failed to process segmentations: `{err}` for taskId: `{task['taskId']}`"
                    )
                    return {"error": err}

                await self.context.labeling.put_labeling_results(
                    session,
                    self.project.org_id,
                    self.project.project_id,
                    stage_name,
                    task_id,
                    (
                        json.dumps(task.get("labels") or [], separators=(",", ":"))
                        if "labels" in task
                        else None
                    ),
                    labels_data_path,
                    labels_map,
                    finalize,
                )

        except ValueError as error:
            log_error(error)
            point_error = deepcopy(task)
            point_error["error"] = error
            return point_error
        return None

    async def _put_tasks(
        self,
        stage_name: str,
        tasks: List[Dict],
        finalize: bool,
        review_result: Optional[bool],
        review_comment: Optional[Comment],
        label_storage_id: str,
        project_label_storage_id: str,
        label_validate: bool,
        prune_segmentations: bool,
        existing_labels: bool,
    ) -> List[Dict]:
        async with get_session() as session:
            coros = [
                self._put_task(
                    session,
                    stage_name,
                    task,
                    finalize,
                    review_result,
                    review_comment,
                    label_storage_id,
                    project_label_storage_id,
                    label_validate,
                    prune_segmentations,
                    existing_labels,
                )
                for task in tasks
            ]
            temp = await gather_with_concurrency(
                10, *coros, progress_bar_name="Uploading tasks", keep_progress_bar=True
            )

        return [val for val in temp if val]

    @check_stage
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
        # pylint: disable=too-many-locals, too-many-branches, too-many-statements

        if not tasks:
            return []

        failed_tasks: List[Dict] = []
        with_labels: List[OutputTask] = []
        without_labels: List[OutputTask] = []
        for task in tasks:
            point = deepcopy(task)
            # Invalid task
            if not (
                isinstance(point, dict)
                and isinstance(point.get("taskId"), str)
                and point["taskId"]
            ):
                logger.warning(f"Task {point} does not have `taskId`")
                failed_tasks.append(point)  # type: ignore
            # Submitted with existing labels
            elif not self.review and existing_labels:
                without_labels.append(point)
            # Rejected
            elif self.review and review_result is not None and not review_result:
                without_labels.append(point)
            # Submitted/Corrected (New label format)
            elif point.get("classification") or (isinstance(point.get("series"), list)):
                point["name"] = "test"
                point["series"] = point.get("series") or [
                    {"name": "test", "items": DUMMY_FILE_PATH}
                ]
                for series in point["series"]:
                    series["name"] = "test"
                    series["items"] = DUMMY_FILE_PATH
                with_labels.append(point)
            # Submitted/Corrected (Old label format)
            elif isinstance(point.get("labels"), list):
                point["name"] = "test"
                point["items"] = [DUMMY_FILE_PATH]  # type: ignore
                with_labels.append(point)
            # Accepted
            elif self.review and review_result:
                without_labels.append(point)
            # Invalid review state
            elif self.review:
                logger.warning(f"Task {point} does not have `review_result`")
                failed_tasks.append(point)  # type: ignore
            # Invalid label state
            else:
                logger.warning(f"Invalid task format {point}")
                failed_tasks.append(point)  # type: ignore

        project_label_storage_id, _ = self.context.project.get_label_storage(
            self.project.org_id, self.project.project_id
        )
        if with_labels:
            if rt_struct:
                converted = asyncio.run(
                    gather_with_concurrency(
                        concurrency,
                        *[
                            convert_rt_struct_to_nii_labels(
                                self.context,
                                self.project.org_id,
                                self.project.taxonomy,
                                [task],
                                StorageMethod.REDBRICK,
                                label_storage_id or project_label_storage_id,
                                label_validate,
                            )
                            for task in tasks
                        ],
                    )
                )
                with_labels = [task[0] for task in converted]

            elif dicom_seg:
                converted = asyncio.run(
                    gather_with_concurrency(
                        concurrency,
                        *[
                            convert_dicom_seg_to_nii_labels(
                                self.context,
                                self.project.org_id,
                                [task],
                                StorageMethod.REDBRICK,
                                label_storage_id or project_label_storage_id,
                            )
                            for task in tasks
                        ],
                    )
                )
                with_labels = [task[0] for task in converted]

            elif mhd:
                converted = asyncio.run(
                    gather_with_concurrency(
                        concurrency,
                        *[
                            convert_mhd_to_nii_labels(
                                self.context,
                                self.project.org_id,
                                [task],
                                StorageMethod.REDBRICK,
                            )
                            for task in tasks
                        ],
                    )
                )
                with_labels = [task[0] for task in converted]

            validated = asyncio.run(
                validate_json(
                    self.context,
                    with_labels,  # type: ignore
                    StorageMethod.REDBRICK,
                    concurrency,
                )
            )

            with_labels_converted: List[Dict]
            if validated:
                with_labels_converted = validated
            else:
                failed_tasks.extend(with_labels)  # type: ignore
                with_labels_converted = []

            failed_tasks.extend(
                asyncio.run(
                    self._put_tasks(
                        stage_name,
                        with_labels_converted,
                        finalize,
                        None,
                        review_comment,
                        label_storage_id or project_label_storage_id,
                        project_label_storage_id,
                        label_validate,
                        prune_segmentations,
                        False,
                    )
                )
            )

        if without_labels:
            failed_tasks.extend(
                asyncio.run(
                    self._put_tasks(
                        stage_name,
                        without_labels,  # type: ignore
                        True,
                        review_result,
                        review_comment,
                        label_storage_id or project_label_storage_id,
                        project_label_storage_id,
                        label_validate,
                        prune_segmentations,
                        existing_labels,
                    )
                )
            )

        return [
            task
            for task in tasks
            if task["taskId"] in {task["taskId"] for task in failed_tasks}
        ]

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
        return self.context.labeling.assign_tasks(
            self.project.org_id,
            self.project.project_id,
            task_ids,
            [email] if email else emails,
            False,
            refresh,
        )

    async def _tasks_to_start(self, task_ids: List[str]) -> None:
        async with get_session() as session:
            coros = [
                self.context.labeling.move_task_to_start(
                    session, self.project.org_id, self.project.project_id, task_id
                )
                for task_id in task_ids
            ]
            await gather_with_concurrency(
                10,
                *coros,
                progress_bar_name="Moving tasks to Start",
                keep_progress_bar=True,
            )

    def move_tasks_to_start(self, task_ids: List[str]) -> None:
        """Move groundtruth tasks back to start."""
        asyncio.run(self._tasks_to_start(task_ids))
