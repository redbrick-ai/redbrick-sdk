"""Public interface to labeling module."""
import functools
from inspect import signature
import json
import asyncio
from typing import Callable, List, Dict, Optional, Any, TypeVar, cast
from copy import deepcopy
from functools import partial

import aiohttp
import tqdm  # type: ignore

from redbrick.common.context import RBContext
from redbrick.common.enums import StorageMethod
from redbrick.utils.upload import process_segmentation_upload, validate_json
from redbrick.utils.logging import log_error, logger
from redbrick.utils.pagination import PaginationIterator
from redbrick.utils.async_utils import gather_with_concurrency
from redbrick.utils.rb_label_utils import clean_rb_label


TFun = TypeVar("TFun", bound=Callable[..., Any])  # pylint: disable=invalid-name


def check_stage(func: TFun) -> TFun:
    """Check if stage exists in project and matches the interface."""

    @functools.wraps(func)
    def wrapper(
        self: "Labeling", *args: Any, **kwargs: Any
    ) -> Optional[Callable[..., Any]]:
        func_args = dict(zip(list(signature(func).parameters.keys())[1:], args))
        func_args.update(kwargs)
        if func_args["stage_name"] not in [stage["stageName"] for stage in self.stages]:
            log_error(
                f"Stage '{func_args['stage_name']}' does not exist in this project, "
                + f"or is not a '{'Review' if self.review else 'Label'}' stage.\n"
                + "If it exists, you may need to use the following:\n>>> "
                + f"project.{'labeling' if self.review else 'review'}.{func.__name__}(...)"
            )
            return None
        return func(self, *args, **kwargs)

    return cast(TFun, wrapper)


class Labeling:
    r"""
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
        ``task_ids``, you can query the tasks using :obj:`~redbrick.export.Export.list_tasks`.

    """

    def __init__(
        self,
        context: RBContext,
        org_id: str,
        project_id: str,
        stages: List[Dict],
        review: bool = False,
    ) -> None:
        """Construct Labeling."""
        self.context = context
        self.org_id = org_id
        self.project_id = project_id
        self.stages = stages
        self.review = review

    @check_stage
    def get_tasks(self, stage_name: str, count: int = 1) -> List[Dict]:
        """
        .. admonition:: Deprecation Notice

            .. deprecated:: 2.11.0

            Use :obj:`~redbrick.export.Export.list_tasks` instead.

        Get tasks assigned to the API Key.

        Get a list of tasks from ``stage_name`` for the current API Key to work upon. If
        the current API Key is not assigned any tasks, calling this method will automatically
        assign tasks to the API Key.

        >>> project = redbrick.get_project(...)
        >>> label_tasks = project.labeling.get_tasks(...)
        >>> review_tasks = project.review.get_tasks...)

        Parameters
        -------------
        stage_name: str
            The name of the stage your want to get tasks from. You can
            find the stage name on the workflow overview on the project
            dashboard.

        count: int = 1
            The number of tasks to retrieve. We recommend keeping this
            < 50.

        Returns
        ----------
        List[Dict]
            Tasks that are queued in this stage. Please see reference doc
            for formats.
            https://docs.redbrickai.com/python-sdk/reference#task-objects
        """
        logger.warning(
            "`Labeling.get_task_queue` method has been deprecated and will be removed "
            + "in a future release. Please use `Export.list_tasks` method instead."
        )
        tasks = self.context.labeling.get_labeling_tasks(
            self.org_id, self.project_id, stage_name, count=count
        )

        def _clean_tasks(task: Dict) -> Dict:
            task_id = task["taskId"]
            labels = json.loads(task.get("taskData", {}).get("labelsData", "[]"))
            labels_cleaned = [clean_rb_label(label) for label in labels]

            items = task["datapoint"]["items"]
            items_presigned = task["datapoint"]["itemsPresigned"]
            name = task["datapoint"]["name"]

            return {
                "taskId": task_id,
                "labels": labels_cleaned,
                "items": items,
                "itemsPresigned": items_presigned,
                "name": name,
            }

        return [_clean_tasks(task) for task in tasks]

    async def _put_task(
        self,
        session: aiohttp.ClientSession,
        stage_name: str,
        task: Dict,
        finalize: bool,
        review_result: Optional[bool],
        project_label_storage_id: str,
        label_storage_id: str,
        label_validate: bool,
        existing_labels: bool,
    ) -> Optional[Dict]:
        task_id = task["taskId"]
        try:
            if self.review and review_result is not None:
                await self.context.labeling.put_review_task_result(
                    session,
                    self.org_id,
                    self.project_id,
                    stage_name,
                    task_id,
                    review_result,
                )
            elif not self.review and existing_labels:
                await self.context.labeling.put_labeling_task_result(
                    session,
                    self.org_id,
                    self.project_id,
                    stage_name,
                    task_id,
                )
            else:
                try:
                    labels_map = await process_segmentation_upload(
                        self.context,
                        session,
                        self.org_id,
                        self.project_id,
                        task,
                        project_label_storage_id,
                        label_storage_id,
                        label_validate,
                    )
                except ValueError as err:
                    logger.warning(
                        f"Failed to process segmentations: `{err}` for taskId: `{task['taskId']}`"
                    )
                    labels_map = None

                await self.context.labeling.put_labeling_results(
                    session,
                    self.org_id,
                    self.project_id,
                    stage_name,
                    task_id,
                    json.dumps(task["labels"], separators=(",", ":")),
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
        project_label_storage_id: str,
        label_storage_id: str,
        label_validate: bool,
        existing_labels: bool,
    ) -> List[Dict]:
        conn = aiohttp.TCPConnector()
        async with aiohttp.ClientSession(connector=conn) as session:
            coros = [
                self._put_task(
                    session,
                    stage_name,
                    task,
                    finalize,
                    review_result,
                    project_label_storage_id,
                    label_storage_id,
                    label_validate,
                    existing_labels,
                )
                for task in tasks
            ]
            temp = await gather_with_concurrency(10, coros, "Uploading tasks")
        await asyncio.sleep(0.250)  # give time to close ssl connections
        return [val for val in temp if val]

    @check_stage
    def put_tasks(
        self,
        stage_name: str,
        tasks: List[Dict],
        *,
        finalize: bool = True,
        existing_labels: bool = False,
        review_result: Optional[bool] = None,
        label_storage_id: Optional[str] = StorageMethod.REDBRICK,
        label_validate: bool = True,
        concurrency: int = 50,
    ) -> List[Dict]:
        """
        Put tasks with new labels or a review result.

        Use this method to programmatically submit tasks with labels in `Label stage`, or to
        programmatically accept/reject/correct tasks in a `Review stage`. If you don't already
        have a list of ``task_id``, you can use :obj:`~redbrick.export.Export.list_tasks` to
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

        tasks: List[Dict]
            Tasks with new labels or review result.

        finalize: bool = True
            Finalize the task. If you want to save the task without submitting, set this to False.

        existing_labels: bool = False
            If True, the tasks will be submitted with their existing labels.
            Applies only to Label stage.

        review_result: Optional[bool] = None
            Accepts or rejects the task based on the boolean value.
            Applies only to Review stage.

        label_storage_id: Optional[str] = None
            Optional label storage id to reference external nifti segmentations.
            Defaults to project settings' annotation storage_id if not specified.

        label_validate: bool = True
            Validate label nifti instances and segment map.

        concurrency: int = 50

        Returns
        ---------------
        List[Dict]
            A list of tasks that failed.
        """
        # pylint: disable=too-many-locals, too-many-branches

        if not tasks:
            return []

        loop = asyncio.get_event_loop()
        failed_tasks: List[Dict] = []
        with_labels: List[Dict] = []
        without_labels: List[Dict] = []
        for task in tasks:
            point = deepcopy(task)
            # Invalid task
            if not (
                isinstance(point, dict)
                and isinstance(point.get("taskId"), str)
                and point["taskId"]
            ):
                logger.warning(f"Task {point} does not have `taskId`")
                failed_tasks.append(point)
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
                    {"name": "test", "items": "test"}
                ]
                for series in point["series"]:
                    series["name"] = "test"
                    series["items"] = "test"
                with_labels.append(point)
            # Submitted/Corrected (Old label format)
            elif isinstance(point.get("labels"), list):
                point["name"] = "test"
                point["items"] = ["test"]
                with_labels.append(point)
            # Accepted
            elif self.review and review_result:
                without_labels.append(point)
            # Invalid review state
            elif self.review:
                logger.warning(f"Task {point} does not have `review_result`")
                failed_tasks.append(point)
            # Invalid label state
            else:
                logger.warning(f"Invalid task format {point}")
                failed_tasks.append(point)

        project_label_storage_id, _ = self.context.project.get_label_storage(
            self.org_id, self.project_id
        )
        if with_labels:
            with_labels = loop.run_until_complete(
                validate_json(
                    self.context,
                    with_labels,
                    StorageMethod.REDBRICK,
                    concurrency,
                )
            )

            failed_tasks.extend(
                loop.run_until_complete(
                    self._put_tasks(
                        stage_name,
                        with_labels,
                        finalize,
                        None,
                        project_label_storage_id,
                        label_storage_id or project_label_storage_id,
                        label_validate,
                        False,
                    )
                )
            )

        if without_labels:
            failed_tasks.extend(
                loop.run_until_complete(
                    self._put_tasks(
                        stage_name,
                        without_labels,
                        True,
                        review_result,
                        project_label_storage_id,
                        label_storage_id or project_label_storage_id,
                        label_validate,
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
        email: Optional[str] = None,
        current_user: bool = False,
        refresh: bool = True,
    ) -> List[Dict]:
        """
        .. admonition:: Deprecation Notice

            .. deprecated:: 2.11.0

            Parameter `current_user` has been deprecated.

        Assign tasks to specified email or current API key.

        Unassigns all users from the task if neither of the ``email`` or ``current_user`` are set.

        >>> project = redbrick.get_project(org_id, project_id, api_key)
        >>> project.labeling.assign_tasks([task_id], email)

        Parameters
        ------------------
        task_ids: List[str]
            List of unique ``task_id`` of the tasks you want to assign.

        email: Optional[str] = None
            The email of the user you want to assign this task to. Make sure the
            user has adequate permissions to be assigned this task in the project.

        current_user: bool = False
            If `True`, will assign the task to the API KEY being used with the SDK.

        refresh: bool = True
            Used for projects with Consensus activated.
            If `True`, will `overwrite` the assignment to the current users.

        Returns
        ---------------
        List[Dict]
            List of affected tasks - [{"taskId", "name", "stageName"}]
        """
        if current_user:
            logger.warning(
                "`current_user` has been deprecated and will be removed in a future release."
            )

        return self.context.labeling.assign_tasks(
            self.org_id,
            self.project_id,
            task_ids,
            [email] if email else None,
            current_user,
            refresh,
        )

    @check_stage
    def get_task_queue(
        self,
        stage_name: str,
        concurrency: int = 50,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        fetch_unassigned: bool = False,
    ) -> List[Dict]:
        """
        .. admonition:: Deprecation Notice

            .. deprecated:: 2.11.0

            Use :obj:`~redbrick.export.Export.list_tasks` instead.

        Get all tasks in queue.

        Returns all the tasks assigned to a particular user and/or
        tasks that are unassigned.

        Parameters
        --------------
        stage_name: str
            The stage for which you want to query the task queue.

        concurrency: int = 50
            The number of tasks to retrieve at a time.
            We recommend keeping this <= 50.

        user_id: Optional[str] = None
            The user id for which you want to query the task queue.
            Will be preferred if both ``user_id`` and ``email`` are set.

        email: Optional[str] = None
            The user email for which you want to query the task queue.
            If both ``user_id`` and ``email`` are None, will query for current API Key.

        fetch_unassigned: bool = False
            Whether to fetch unassigned tasks.

        Returns
        ---------------
        List[Dict]
            List of tasks in queue - [{"taskId", "name", "createdAt"}]
        """
        logger.warning(
            "`Labeling.get_task_queue` method has been deprecated and will be removed "
            + "in a future release. Please use `Export.list_tasks` method instead."
        )
        my_iter = PaginationIterator(
            partial(  # type: ignore
                self.context.export.task_search,
                self.org_id,
                self.project_id,
                stage_name,
                None,
                {"userId": user_id or email or self.context.key_id},
                False,
            ),
            concurrency,
        )

        with tqdm.tqdm(
            my_iter, unit=" datapoints", desc="Fetching assigned tasks"
        ) as progress:
            datapoints = [
                {
                    "taskId": task["taskId"],
                    "name": task["datapoint"]["name"],
                    "assignedTo": (
                        (task["currentStageSubTask"] or {}).get("assignedTo") or {}
                    ).get("email"),
                    "status": (task["currentStageSubTask"] or {}).get("state"),
                    "items": task["datapoint"]["items"],
                    "itemsPresigned": task["datapoint"]["itemsPresigned"],
                    "createdAt": task["createdAt"],
                }
                for task in progress
            ]

        if fetch_unassigned:
            my_iter = PaginationIterator(
                partial(  # type: ignore
                    self.context.export.task_search,
                    self.org_id,
                    self.project_id,
                    stage_name,
                    None,
                    {"userId": None},
                    False,
                ),
                concurrency,
            )

            with tqdm.tqdm(
                my_iter, unit=" datapoints", desc="Fetching unassigned tasks"
            ) as progress:
                datapoints += [
                    {
                        "taskId": task["taskId"],
                        "name": task["datapoint"]["name"],
                        "assignedTo": None,
                        "status": (task["currentStageSubTask"] or {}).get("state"),
                        "items": task["datapoint"]["items"],
                        "itemsPresigned": task["datapoint"]["itemsPresigned"],
                        "createdAt": task["createdAt"],
                    }
                    for task in progress
                ]

        return datapoints

    async def _tasks_to_start(self, task_ids: List[str]) -> None:
        conn = aiohttp.TCPConnector()
        async with aiohttp.ClientSession(connector=conn) as session:
            coros = [
                self.context.labeling.move_task_to_start(
                    session, self.org_id, self.project_id, task_id
                )
                for task_id in task_ids
            ]
            await gather_with_concurrency(10, coros, "Moving tasks to Start")
        await asyncio.sleep(0.250)  # give time to close ssl connections

    def move_tasks_to_start(self, task_ids: List[str]) -> None:
        """Move groundtruth tasks back to start."""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._tasks_to_start(task_ids))
