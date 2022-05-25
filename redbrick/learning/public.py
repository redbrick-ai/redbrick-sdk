"""Public interface to learning module."""
import os
import json
import asyncio
from typing import Dict, List, Optional, Tuple, Callable, Any, Union, TypeVar, cast
from functools import partial, wraps
from copy import deepcopy

import aiohttp
import tqdm

from redbrick.common.constants import MAX_CONCURRENCY
from redbrick.utils.files import NIFTI_FILE_TYPES, upload_files
from redbrick.common.context import RBContext
from redbrick.common.enums import TaskStates
from redbrick.utils.pagination import PaginationIterator
from redbrick.utils.rb_label_utils import clean_rb_label
from redbrick.utils.async_utils import gather_with_concurrency
from redbrick.utils.logging import (
    print_error,
    print_info,
    print_warning,
    handle_exception,
)

Func = TypeVar("Func", bound=Callable[..., Any])


def check_learning_stage(func: Func) -> Func:
    """Implement decorator to check if active learning is enabled for current project."""

    @wraps(func)
    def wrap(obj: Union["Learning", "Learning2"], *args: Any, **kwargs: Any) -> Any:
        if not obj.stage_name:
            raise Exception("No stage available for active learning in this project.")
        return func(obj, *args, **kwargs)

    return cast(Func, wrap)


class Learning:
    """Perform active learning and upload the results with the RedBrick API."""

    def __init__(
        self, context: RBContext, org_id: str, project_id: str, stage_name: str = ""
    ) -> None:
        """Construct Learning module."""
        self.context = context
        self.org_id = org_id
        self.project_id = project_id
        self.stage_name = stage_name

    @handle_exception
    @check_learning_stage
    def get_learning_info(self) -> Dict:
        """
        Get a dictionary with lightly parsed redbrick response.

        The dictonary has fields:
            labeled
            unlabeled
            taxonomy
            cycle
        """
        cycle = self.context.learning.check_for_job(
            self.org_id, self.project_id, self.stage_name
        )
        if not cycle:
            raise Exception("No available jobs")

        my_iter = PaginationIterator(
            partial(
                self.context.learning.get_batch_of_tasks,
                self.org_id,
                self.project_id,
                self.stage_name,
                100,
            )
        )
        taxonomy, td_type = self.context.learning.get_taxonomy_and_type(
            self.org_id, self.project_id, self.stage_name
        )

        def _parse_labeled_entry(item: Dict) -> Dict:
            datapoint = item.get("datapoint", {}) or {}
            items_presigned = datapoint.get("itemsPresigned", []) or []
            name = datapoint.get("name")
            items = datapoint.get("items", []) or []
            task_id = item.get("taskId")
            groundtruth = item.get("groundTruth", {}) or {}
            labels = [
                clean_rb_label(label)
                for label in json.loads(groundtruth.get("labelsData", "[]") or "[]")
            ]

            return {
                "taskId": task_id,
                "items": items,
                "itemsPresigned": items_presigned,
                "name": name,
                "labels": labels,
            }

        def _parse_unlabeled_entry(item: Dict) -> Dict:
            datapoint = item.get("datapoint", {}) or {}
            items_presigned = datapoint.get("itemsPresigned", []) or []
            name = datapoint.get("name")
            items = datapoint.get("items", []) or []
            task_id = item.get("taskId")
            return {
                "taskId": task_id,
                "items": items,
                "itemsPresigned": items_presigned,
                "name": name,
            }

        labeled: List[Dict] = []
        unlabeled: List[Dict] = []

        print_info("Downloading tasks for active learning")
        for entry in tqdm.tqdm(my_iter, unit=" tasks"):
            if entry.get("groundTruth"):
                labeled.append(_parse_labeled_entry(entry))
            else:
                unlabeled.append(_parse_unlabeled_entry(entry))

        return {
            "labeled": labeled,
            "unlabeled": unlabeled,
            "taxonomy": taxonomy,
            "cycle": cycle,
            "type": td_type,
        }

    async def _update_task(
        self, session: aiohttp.ClientSession, cycle: int, task: Dict
    ) -> Optional[Dict]:
        """Attempt to update task."""
        try:
            await self.context.learning.send_batch_learning_results_async(
                session,
                self.org_id,
                self.project_id,
                self.stage_name,
                cycle,
                [task],
            )
        except ValueError as error:
            print_error(error)
            point_error = deepcopy(task)
            point_error["error"] = error
            return point_error
        return None

    async def _update_tasks(self, cycle: int, tasks: List[Dict]) -> List[Dict]:
        failed = []
        conn = aiohttp.TCPConnector(limit=MAX_CONCURRENCY)
        async with aiohttp.ClientSession(connector=conn) as session:
            coros = [self._update_task(session, cycle, task) for task in tasks]
            temp = await gather_with_concurrency(
                100, coros, "Updating tasks with priorities"
            )

            for val in temp:
                if val:
                    failed.append(val)

        await asyncio.sleep(0.250)  # give time to close ssl connections
        return failed

    @handle_exception
    @check_learning_stage
    def update_tasks(self, cycle: int, tasks: List[Dict]) -> List[Dict]:
        """
        Update tasks with new score and labels.

        Return any tasks that experienced issues.
        """
        loop = asyncio.get_event_loop()
        temp = loop.run_until_complete(self._update_tasks(cycle, tasks))

        # update cycle
        self.context.learning.set_cycle_status(
            self.org_id, self.project_id, self.stage_name, cycle, "DONE"
        )
        return temp


class Learning2:
    """Reimplement Learning."""

    def __init__(
        self, context: RBContext, org_id: str, project_id: str, stage_name: str = ""
    ) -> None:
        """Construct Learning module."""
        self.context = context
        self.org_id = org_id
        self.project_id = project_id
        self.stage_name = stage_name

    @handle_exception
    @check_learning_stage
    def check_is_processing(self) -> bool:
        """Check if a job is in process already."""
        result = self.context.learning2.check_for_job(self.org_id, self.project_id)
        return bool(result.get("isProcessing"))

    @handle_exception
    @check_learning_stage
    def check_for_job(self, min_new_tasks: int = 100) -> bool:
        """Return true if there is a new job available."""
        result = self.context.learning2.check_for_job(self.org_id, self.project_id)
        if (
            result.get("newTasks", 0) >= min_new_tasks
            and result.get("isProcessing") is False
        ):
            return True
        if result.get("isProcessing") is True and (
            result.get("newTasks", 0) + result.get("newTasksProcessing", 0)
            >= min_new_tasks
        ):
            return True

        return False

    @handle_exception
    @check_learning_stage
    def get_learning_info(
        self, min_new_tasks: int = 100, concurrency: int = 100
    ) -> Dict:
        """
        Get a dictionary with lightly parsed redbrick response.

        The dictonary has fields:
            labeled
            unlabeled
            taxonomy
            type
        """
        if not self.check_for_job(min_new_tasks):
            raise Exception("Not enough new tasks since last training cycle.")

        taxonomy, td_type = self.context.learning2.get_taxonomy_and_type(
            self.org_id, self.project_id
        )

        def _filter_active_learning_tasks(
            org_id: str,
            project_id: str,
            stage_name: str,
            concurrency: int,
            cursor: Optional[str],
        ) -> Tuple[List[Dict], str]:
            entries, new_cursor = self.context.labeling.get_tasks_queue(
                org_id, project_id, stage_name, concurrency, cursor
            )
            return [
                item for item in entries if item["state"] == TaskStates.UNASSIGNED.value
            ], new_cursor

        my_queue_iter = PaginationIterator(
            partial(
                _filter_active_learning_tasks,
                self.org_id,
                self.project_id,
                self.stage_name,
                concurrency,
            )
        )
        tasks_in_queue = self.context.labeling.get_task_queue_count(
            self.org_id, self.project_id, self.stage_name, True
        )
        general_info = self.context.export.get_output_info(self.org_id, self.project_id)

        my_finished_iter = PaginationIterator(
            partial(
                self.context.export.get_datapoints_output,
                self.org_id,
                self.project_id,
                concurrency,
            )
        )

        def _parse_labeled_entry(item: Dict) -> Dict:
            items_presigned = item.get("itemsPresigned", []) or []
            name = item.get("name")
            items = item.get("items", []) or []
            task = item.get("task", {}) or {}
            task_id = task.get("taskId")
            label_data = item.get("labelData", {}) or {}
            labels = [
                clean_rb_label(label)
                for label in json.loads(label_data.get("labelsData", "[]") or "[]")
            ]

            return {
                "taskId": task_id,
                "items": items,
                "itemsPresigned": items_presigned,
                "name": name,
                "labels": labels,
                "labelsMap": label_data.get("labelsMap", []) or [],
            }

        def _parse_unlabeled_entry(item: Dict) -> Dict:
            datapoint = item.get("datapoint", {}) or {}
            items_presigned = datapoint.get("itemsPresigned", []) or []
            name = datapoint.get("name")
            items = datapoint.get("items", []) or []
            task_id = item.get("taskId")
            return {
                "taskId": task_id,
                "items": items,
                "status": item.get("state"),
                "itemsPresigned": items_presigned,
                "name": name,
            }

        print_info("Downloading unfinished tasks")
        unlabeled = [
            _parse_unlabeled_entry(item)
            for item in tqdm.tqdm(my_queue_iter, unit=" tasks", total=tasks_in_queue)
        ]

        print_info("Downloading finished tasks")
        labeled = [
            _parse_labeled_entry(item)
            for item in tqdm.tqdm(
                my_finished_iter,
                unit=" tasks",
                total=general_info["datapointCount"],
            )
        ]

        return {
            "labeled": labeled,
            "unlabeled": unlabeled,
            "taxonomy": taxonomy,
            "type": td_type,
        }

    async def _update_task2(
        self, session: aiohttp.ClientSession, task: Dict
    ) -> Optional[Dict]:
        """Attempt to update task."""
        try:
            task_input = deepcopy(task)
            if "labels" in task_input:
                task_input["labelsData"] = json.dumps(task_input["labels"])
                del task_input["labels"]

            labels_path: Optional[str] = None
            if "labelsPath" in task_input:
                labels_path = task_input["labelsPath"]
                del task_input["labelsPath"]
            if (
                labels_path
                and (labels_path.endswith(".nii") or labels_path.endswith(".nii.gz"))
                and os.path.isfile(labels_path)
            ):
                file_type = NIFTI_FILE_TYPES["nii"]
                presigned = await self.context.labeling.presign_labels_path(
                    session,
                    self.org_id,
                    self.project_id,
                    task_input["taskId"],
                    file_type,
                )
                if (
                    await upload_files(
                        [(labels_path, presigned["presignedUrl"], file_type)],
                        "Uploading labels",
                        False,
                    )
                )[0]:
                    task_input["labelsPath"] = presigned["filePath"]
            await self.context.learning2.update_prelabels_and_priorities(
                session, self.org_id, self.project_id, self.stage_name, [task_input]
            )
        except ValueError as error:
            print_error(error)
            point_error = deepcopy(task)
            point_error["error"] = error
            return point_error
        return None

    async def _update_tasks2(self, tasks: List[Dict]) -> List[Dict]:
        failed = []
        conn = aiohttp.TCPConnector(limit=MAX_CONCURRENCY)
        async with aiohttp.ClientSession(connector=conn) as session:
            coros = [self._update_task2(session, task) for task in tasks]
            temp = await gather_with_concurrency(
                10, coros, "Updating tasks with priorities"
            )

            for val in temp:
                if val:
                    failed.append(val)
        await asyncio.sleep(0.250)  # give time to close ssl connections
        return failed

    @handle_exception
    @check_learning_stage
    def update_tasks(self, cycle: int, tasks: List[Dict]) -> List[Dict]:
        """
        Update tasks with new score and labels.

        Return any tasks that experienced issues.
        """
        if cycle != 1:
            print_warning("Use of cycle field is deprecated")
        _ = cycle  # deprecated

        # backwards compatibility
        for task in tasks:
            if task.get("score"):
                task["priority"] = task["score"]
                del task["score"]

        loop = asyncio.get_event_loop()
        temp = loop.run_until_complete(self._update_tasks2(tasks))
        return temp

    @handle_exception
    @check_learning_stage
    def start_processing(self) -> None:
        """Signal to RedBrick AI that the training has begun."""
        self.context.learning2.start_processing(self.org_id, self.project_id)

    @handle_exception
    @check_learning_stage
    def end_processing(self) -> None:
        """Signal to RedBrick AI that the training has end."""
        self.context.learning2.end_processing(self.org_id, self.project_id)
