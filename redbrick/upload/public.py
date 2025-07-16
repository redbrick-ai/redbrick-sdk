"""Public interface to upload module."""

import asyncio
import os
import sys
from copy import deepcopy
from typing import List, Dict, Optional
import json

import aiohttp

from redbrick.common.entities import RBProject
from redbrick.common.constants import DUMMY_FILE_PATH, MAX_CONCURRENCY
from redbrick.common.enums import ImportTypes
from redbrick.common.storage import StorageMethod
from redbrick.common.upload import Upload
from redbrick.upload.interact import (
    create_tasks,
    prepare_json_files,
    upload_datapoints,
    validate_json,
)
from redbrick.utils.rb_event_utils import comment_format
from redbrick.utils.upload import (
    convert_mhd_to_nii_labels,
    convert_rt_struct_to_nii_labels,
    convert_dicom_seg_to_nii_labels,
    process_segmentation_upload,
)
from redbrick.utils.async_utils import gather_with_concurrency, get_session
from redbrick.utils.logging import log_error, logger
from redbrick.utils.files import get_file_type, is_dicom_file
from redbrick.types.task import InputTask, OutputTask, CommentPin


class UploadImpl(Upload):
    """
    Primary interface for uploading to a project.

    .. code:: python

        >>> project = redbrick.get_project(api_key="", org_id="", project_id="")
        >>> project.upload
    """

    def __init__(self, project: RBProject) -> None:
        """Construct Upload object."""
        self.project = project
        self.context = self.project.context

    def create_datapoints(
        self,
        storage_id: str,
        points: List[InputTask],
        *,
        is_ground_truth: bool = False,
        segmentation_mapping: Optional[Dict] = None,
        rt_struct: bool = False,
        dicom_seg: bool = False,
        mhd: bool = False,
        label_storage_id: Optional[str] = None,
        label_validate: bool = False,
        prune_segmentations: bool = False,
        concurrency: int = 50,
    ) -> List[Dict]:
        """
        Create datapoints in project.

        Upload data, and optionally annotations, to your project. Please visit
        `our documentation <https://sdk.redbrickai.com/formats/index.html#import>`_
        to understand the format for ``points``.

        .. code:: python

            project = redbrick.get_project(org_id, project_id, api_key, url)
            points = [
                {
                    "name": "...",
                    "series": [
                        {
                            "items": "...",

                            # These fields are needed for importing segmentations.
                            "segmentations": "...",
                            "segmentMap": {...}
                        }
                    ]
                }
            ]
            project.upload.create_datapoints(storage_id, points)


        Parameters
        --------------
        storage_id: str
            Your RedBrick AI external storage_id. This can be found under the Storage Tab
            on the RedBrick AI platform. To directly upload images to rbai,
            use redbrick.StorageMethod.REDBRICK.

        points: List[:obj:`~redbrick.types.task.InputTask`]
            Please see the RedBrick AI reference documentation for overview of the format.
            https://sdk.redbrickai.com/formats/index.html#import.
            All the fields with `annotation` information are optional.

        is_ground_truth: bool = False
            If labels are provided in ``points``, and this parameters
            is set to true, the labels will be added to the Ground Truth stage.

        segmentation_mapping: Optional[Dict] = None
            Optional mapping of semantic_mask segmentation class ids and RedBrick categories.

        rt_struct: bool = False
            Upload segmentations from DICOM RT-Struct files.

        dicom_seg: bool = False
            Upload segmentations from DICOM Segmentation files.

        mhd: bool = False
            Upload segmentations from MHD files.

        label_storage_id: Optional[str] = None
            Optional label storage id to reference nifti segmentations.
            Defaults to items storage_id if not specified.

        label_validate: bool = False
            Validate label nifti instances and segment map.

        prune_segmentations: bool = False
            Prune segmentations that are not part of the series.

        concurrency: int = 50

        Returns
        -------------
        List[Dict]
            List of task objects with key `response` if successful, else `error`

        Note
        ----------
            1. If doing direct upload, please use ``redbrick.StorageMethod.REDBRICK``
            as the storage id. Your items path must be a valid path to a locally stored image.

            2. When doing direct upload i.e. ``redbrick.StorageMethod.REDBRICK``,
            if you didn't specify a "name" field in your datapoints object,
            we will assign the "items" path to it.
        """
        return upload_datapoints(
            context=self.context,
            org_id=self.project.org_id,
            workspace_id=None,
            project_id=self.project.project_id,
            taxonomy=self.project.taxonomy,
            storage_id=storage_id,
            points=points,
            is_ground_truth=is_ground_truth,
            segmentation_mapping=segmentation_mapping,
            rt_struct=rt_struct,
            dicom_seg=dicom_seg,
            mhd=mhd,
            label_storage_id=label_storage_id,
            label_validate=label_validate,
            prune_segmentations=prune_segmentations,
            concurrency=concurrency,
        )

    async def _delete_tasks(self, task_ids: List[str], concurrency: int) -> bool:
        async with get_session() as session:
            coros = [
                self.context.upload.delete_tasks(
                    session,
                    self.project.org_id,
                    self.project.project_id,
                    task_ids[batch : batch + concurrency],
                )
                for batch in range(0, len(task_ids), concurrency)
            ]
            success = await gather_with_concurrency(
                10, *coros, progress_bar_name="Deleting tasks", keep_progress_bar=True
            )

        return all(success)

    def delete_tasks(self, task_ids: List[str], concurrency: int = 50) -> bool:
        """Delete project tasks based on task ids.

        >>> project = redbrick.get_project(org_id, project_id, api_key, url)
        >>> project.upload.delete_tasks([...])

        Parameters
        --------------
        task_ids: List[str]
            List of task ids to delete.

        concurrency: int = 50
            The number of tasks to delete at a time.
            We recommend keeping this less than or equal to 50.

        Returns
        -------------
        bool
            True if successful, else False.
        """
        concurrency = min(concurrency, 50)
        return asyncio.run(self._delete_tasks(task_ids, concurrency))

    async def _delete_tasks_by_name(
        self, task_names: List[str], concurrency: int
    ) -> bool:
        async with get_session() as session:
            coros = [
                self.context.upload.delete_tasks_by_name(
                    session,
                    self.project.org_id,
                    self.project.project_id,
                    task_names[batch : batch + concurrency],
                )
                for batch in range(0, len(task_names), concurrency)
            ]
            success = await gather_with_concurrency(
                10, *coros, progress_bar_name="Deleting tasks", keep_progress_bar=True
            )

        return all(success)

    def delete_tasks_by_name(
        self, task_names: List[str], concurrency: int = 50
    ) -> bool:
        """Delete project tasks based on task names.

        >>> project = redbrick.get_project(org_id, project_id, api_key, url)
        >>> project.upload.delete_tasks_by_name([...])

        Parameters
        --------------
        task_names: List[str]
            List of task names to delete.

        concurrency: int = 50
            The number of tasks to delete at a time.
            We recommend keeping this less than or equal to 50.

        Returns
        -------------
        bool
            True if successful, else False.
        """
        concurrency = min(concurrency, 50)
        return asyncio.run(self._delete_tasks_by_name(task_names, concurrency))

    async def generate_items_list(
        self,
        items_list: List[List[str]],
        import_file_type: str,
        as_study: bool,
        concurrency: int = 50,
    ) -> List[Dict]:
        """Generate items list from local files."""
        # pylint: disable=too-many-locals, too-many-branches
        logger.debug(f"Concurrency: {concurrency} for {len(items_list)} items")
        grouped_items_list: Dict[str, List[str]] = {}
        for items in items_list:
            if not items:
                continue
            items_dir = os.path.dirname(items[0])
            if as_study:
                items_dir = os.path.dirname(items_dir)

            if items_dir not in grouped_items_list:
                grouped_items_list[items_dir] = []
            grouped_items_list[items_dir].extend(items)

        logger.debug(f"Grouped items list: {len(grouped_items_list)}")

        items_list = list(grouped_items_list.values())
        total_groups = len(items_list)
        items_map: Dict[str, str] = {}

        if import_file_type == ImportTypes.DICOM3D:
            for items in items_list:
                for idx, item in enumerate(items):
                    file_ext, file_type = get_file_type(item)
                    if (
                        not file_ext or file_type != "application/dicom"
                    ) and is_dicom_file(item):
                        items[idx] = item + ".dcm"
                        items_map[items[idx]] = item

        is_win = sys.platform.startswith("win")
        async with get_session() as session:
            coros = [
                self.context.upload.generate_items_list(
                    session,
                    [
                        item
                        for items in items_list[batch : batch + concurrency]
                        for item in items
                    ],
                    import_file_type,
                    as_study,
                    is_win,
                )
                for batch in range(0, total_groups, concurrency)
            ]
            outputs = await gather_with_concurrency(MAX_CONCURRENCY, *coros)

        output_data: List[Dict] = []
        for output in outputs:
            output_data.extend(json.loads(output))

        if import_file_type == ImportTypes.DICOM3D:
            for data in output_data:
                for idx, item in enumerate(data["items"]):
                    if item in items_map:
                        data["items"][idx] = items_map[item]

        return output_data

    def update_task_items(
        self,
        storage_id: str,
        points: List[OutputTask],
        concurrency: int = 50,
        append: bool = False,
    ) -> List[Dict]:
        """
        Update task items, meta data, heat maps, transforms, etc. for the mentioned task ids.

        .. code:: python

            project = redbrick.get_project(org_id, project_id, api_key, url)
            points = [
                {
                    "taskId": "...",
                    "series": [
                        {
                            "items": "...",
                        }
                    ]
                }
            ]
            project.upload.update_task_items(storage_id, points)


        Parameters
        --------------
        storage_id: str
            Your RedBrick AI external storage_id. This can be found under the Storage Tab
            on the RedBrick AI platform. To directly upload images to rbai,
            use redbrick.StorageMethod.REDBRICK.

        points: List[:obj:`~redbrick.types.task.InputTask`]
            List of objects with `taskId` and `series`, where `series` contains
            a list of `items` paths to be updated for the task.

        concurrency: int = 50

        append: bool = False
            If True, the series will be appended to the existing series.
            If False, the series will replace the existing series.

        Returns
        -------------
        List[Dict]
            List of task objects with key `response` if successful, else `error`

        Note
        ----------
            1. If doing direct upload, please use ``redbrick.StorageMethod.REDBRICK``
            as the storage id. Your items path must be a valid path to a locally stored image.
        """
        local_points = deepcopy(points)
        for point in local_points:
            point["series"] = point.get("series") or [{"items": DUMMY_FILE_PATH}]
            for series in point["series"]:
                if not series.get("items"):
                    series["items"] = DUMMY_FILE_PATH

        converted_points = prepare_json_files(
            context=self.context,
            org_id=self.project.org_id,
            taxonomy=self.project.taxonomy,
            files_data=[local_points],  # type: ignore
            storage_id=storage_id,
            label_storage_id=StorageMethod.REDBRICK,
            concurrency=concurrency,
        )

        for converted_point in converted_points:
            if not any(
                item == DUMMY_FILE_PATH
                for item in (converted_point.get("items", []) or [])
            ):
                continue
            converted_point.pop("items", None)
            for info in converted_point.get("seriesInfo", []) or []:
                info.pop("itemsIndices", None)

        return asyncio.run(
            create_tasks(
                context=self.context,
                org_id=self.project.org_id,
                workspace_id=None,
                project_id=self.project.project_id,
                points=converted_points,
                segmentation_mapping={},
                is_ground_truth=False,
                storage_id=storage_id,
                label_storage_id=storage_id,
                concurrency=concurrency,
                update_items=True,
                append=append,
            )
        )

    def import_tasks_from_workspace(
        self, source_project_id: str, task_ids: List[str], with_labels: bool = False
    ) -> None:
        """
        Import tasks from another project in the same workspace.

        .. code:: python

            project = redbrick.get_project(org_id, project_id, api_key, url)
            project.upload.import_tasks_from_workspace(source_project_id, task_ids)


        Parameters
        --------------
        source_project_id: str
            The source project id from which tasks are to be imported.

        task_ids: List[str]
            List of task ids to be imported.

        with_labels: bool = False
            If True, the labels will also be imported.

        Returns
        -------------
        None
        """
        self.context.upload.import_tasks_from_workspace(
            self.project.org_id,
            self.project.project_id,
            source_project_id,
            [{"taskId": task_id} for task_id in task_ids],
            with_labels,
        )

    async def _update_tasks_priorities(
        self, tasks: List[Dict], concurrency: int
    ) -> List[str]:
        async with get_session() as session:
            coros = [
                self.context.upload.update_priority(
                    session,
                    self.project.org_id,
                    self.project.project_id,
                    tasks[batch : batch + concurrency],
                )
                for batch in range(0, len(tasks), concurrency)
            ]
            errors = await gather_with_concurrency(
                10,
                *coros,
                progress_bar_name="Updating tasks' priorities",
                keep_progress_bar=True,
            )

        return [error for error in errors if error]

    def update_tasks_priority(self, tasks: List[Dict], concurrency: int = 50) -> None:
        """
        Update tasks' priorities.
        Used to determine how the tasks get assigned to annotators/reviewers in auto-assignment.

        Parameters
        --------------
        tasks: List[Dict]
            List of taskIds and their priorities.
            - [{"taskId": str, "priority": float([0, 1]), "user"?: str}]

        concurrency: int = 50
            The number of tasks to update at a time.
            We recommend keeping this less than or equal to 50.
        """
        concurrency = min(concurrency, 50)
        errors = asyncio.run(self._update_tasks_priorities(tasks, concurrency))

        if errors:
            log_error(errors[0])

    async def _update_task_labels(
        self,
        session: aiohttp.ClientSession,
        task: Dict,
        label_storage_id: str,
        project_label_storage_id: str,
        label_validate: bool,
        prune_segmentations: bool,
        finalize: bool,
        time_spent_ms: Optional[int],
        extra_data: Optional[Dict],
    ) -> Optional[Dict]:
        # pylint: disable=too-many-locals
        task_id = task["taskId"]
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

        try:
            await self.context.upload.update_labels(
                session,
                self.project.org_id,
                self.project.project_id,
                task_id,
                (
                    json.dumps(task.get("labels") or [], separators=(",", ":"))
                    if "labels" in task
                    else None
                ),
                labels_data_path,
                labels_map,
                finalize,
                time_spent_ms,
                extra_data,
            )

        except ValueError as error:
            log_error(error)
            point_error = deepcopy(task)
            point_error["error"] = error
            return point_error
        return None

    async def _update_tasks_labels(
        self,
        tasks: List[Dict],
        label_storage_id: str,
        project_label_storage_id: str,
        label_validate: bool,
        prune_segmentations: bool,
        finalize: bool,
        time_spent_ms: Optional[int],
        extra_data: Optional[Dict],
    ) -> List[Dict]:
        async with get_session() as session:
            coros = [
                self._update_task_labels(
                    session,
                    task,
                    label_storage_id,
                    project_label_storage_id,
                    label_validate,
                    prune_segmentations,
                    finalize,
                    time_spent_ms,
                    extra_data,
                )
                for task in tasks
            ]
            temp = await gather_with_concurrency(
                10, *coros, progress_bar_name="Updating tasks", keep_progress_bar=True
            )

        return [val for val in temp if val]

    def update_tasks_labels(
        self,
        tasks: List[OutputTask],
        *,
        rt_struct: bool = False,
        dicom_seg: bool = False,
        mhd: bool = False,
        label_storage_id: Optional[str] = StorageMethod.REDBRICK,
        label_validate: bool = False,
        prune_segmentations: bool = False,
        concurrency: int = 50,
        finalize: bool = False,
        time_spent_ms: Optional[int] = None,
        extra_data: Optional[Dict] = None,
    ) -> None:
        """Update tasks labels at any point in project pipeline.

        .. code:: python

            project = redbrick.get_project(...)
            tasks = [
                {
                    "taskId": "...",
                    "series": [{...}]
                },
            ]

            # Overwrite labels in tasks
            project.upload.update_tasks_labels(tasks)


        Parameters
        --------------
        points: List[:obj:`~redbrick.types.task.OutputTask`]
            Please see the RedBrick AI reference documentation for overview of the format.
            https://sdk.redbrickai.com/formats/index.html#export.
            All the fields with `annotation` information are optional.

        rt_struct: bool = False
            Upload segmentations from DICOM RT-Struct files.

        dicom_seg: bool = False
            Upload segmentations from DICOM Segmentation files.

        mhd: bool = False
            Upload segmentations from MHD files.

        label_storage_id: Optional[str] = None
            Optional label storage id to reference nifti segmentations.
            Defaults to project annnotation storage_id if not specified.

        label_validate: bool = False
            Validate label nifti instances and segment map.

        prune_segmentations: bool = False
            Prune segmentations that are not part of the series.

        concurrency: int = 50

        finalize: bool = False
            Submit the task in current stage.

        time_spent_ms: Optional[int] = None
            Time spent on the task in milliseconds.

        extra_data: Optional[Dict] = None
            Extra data to be stored along with the task.
        """
        # pylint: disable=too-many-locals
        if not tasks:
            return

        project_label_storage_id, _ = self.context.project.get_label_storage(
            self.project.org_id, self.project.project_id
        )

        converted_tasks = tasks
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
            converted_tasks = [task[0] for task in converted]

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
            converted_tasks = [task[0] for task in converted]

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
            converted_tasks = [task[0] for task in converted]

        points: List[OutputTask] = []
        for task in converted_tasks:
            point = deepcopy(task)
            # Invalid task
            if not (
                isinstance(point, dict)
                and isinstance(point.get("taskId"), str)
                and point["taskId"]
                and (
                    point.get("classification") or isinstance(point.get("series"), list)
                )
            ):
                logger.warning(f"Task {point} is invalid")
                continue

            point["name"] = point.get("name", "test")
            point["series"] = point.get("series") or [{"items": DUMMY_FILE_PATH}]
            for series in point.get("series", []):
                series["items"] = series.get("items", DUMMY_FILE_PATH)
            points.append(point)

        if not points:
            return

        validated = asyncio.run(
            validate_json(
                self.context,
                points,  # type: ignore
                StorageMethod.REDBRICK,
                concurrency,
            )
        )

        points_converted = validated if validated else []
        asyncio.run(
            self._update_tasks_labels(
                points_converted,
                label_storage_id or project_label_storage_id,
                project_label_storage_id,
                label_validate,
                prune_segmentations,
                finalize,
                time_spent_ms,
                extra_data,
            )
        )

    async def _send_to_stage(
        self, task_ids: List[str], stage_name: str, concurrency: int
    ) -> List[str]:
        async with get_session() as session:
            coros = [
                self.context.upload.send_tasks_to_stage(
                    session,
                    self.project.org_id,
                    self.project.project_id,
                    task_ids[batch : batch + concurrency],
                    stage_name,
                )
                for batch in range(0, len(task_ids), concurrency)
            ]
            responses = await gather_with_concurrency(
                10,
                *coros,
                progress_bar_name=f"Sending tasks to {stage_name} ({concurrency} per batch)",
                keep_progress_bar=True,
            )

        return [response for response in responses if response]

    def send_tasks_to_stage(
        self, task_ids: List[str], stage_name: str, concurrency: int = 50
    ) -> None:
        """Send tasks to different stage.


        Parameters
        --------------
        task_ids: List[str]
            List of tasks to move.

        stage_name: str
            The stage to which you want to move the tasks.
            Use "END" to move tasks to ground truth.

        concurrency: int = 50
            Batch size per request.
        """
        stage_names = [stage.stage_name for stage in self.project.stages] + [
            "ARCHIVED",
            "END",
        ]
        if stage_name not in stage_names:
            raise ValueError(f"Stage {stage_name} not found in project")

        errors = asyncio.run(
            self._send_to_stage(task_ids, stage_name, min(concurrency, 50))
        )
        if errors:
            log_error(errors[0])

    def import_from_dataset(
        self,
        dataset_name: str,
        *,
        import_id: Optional[str] = None,
        series_ids: Optional[List[str]] = None,
        group_by_study: bool = False,
        is_ground_truth: bool = False,
    ) -> None:
        """Import tasks from a dataset for a given import_id or list of series_ids.

        Parameters
        --------------
        dataset_name: str
            The name of the dataset to import from.

        import_id: Optional[str] = None
            The import id of the dataset to import from.

        series_ids: Optional[List[str]] = None
            The series ids to import from the dataset.

        group_by_study: bool = False
            Whether to group the tasks by study.

        is_ground_truth: bool = False
            Whether to import the tasks as ground truth.
        """
        error = self.context.upload.import_from_dataset(
            self.project.org_id,
            dataset_name,
            None,
            self.project.project_id,
            import_id,
            series_ids,
            group_by_study,
            is_ground_truth,
        )
        if error:
            log_error(error)

    def create_comment(
        self,
        task_id: str,
        text_comment: str,
        reply_to_comment_id: Optional[str] = None,
        comment_pin: Optional[CommentPin] = None,
        label_id: Optional[str] = None,
    ) -> Dict:
        """Create a task comment.

        Parameters
        --------------
        task_id: str
            The task id.

        text_comment: str
            The comment to create.

        reply_to_comment_id: Optional[str] = None
            The comment id to reply to.

        comment_pin: Optional[:obj:`~redbrick.types.task.CommentPin`] = None
            The pin to add to the comment.

        label_id: Optional[str] = None
            Label ID for entity-level comments.

        Returns
        -------------
        Dict
            The comment object.
        """
        task = next(self.project.export.list_tasks(task_id=task_id), None)
        if not task:
            raise ValueError("Task not found")

        comment = self.context.upload.create_comment(
            self.project.org_id,
            self.project.project_id,
            task_id,
            task["currentStageName"],
            text_comment,
            reply_to_comment_id,
            comment_pin,
            label_id,
        )
        if not comment:
            raise ValueError("Failed to create comment")

        return comment_format(comment, {})

    def delete_comment(self, task_id: str, comment_id: str) -> None:
        """Delete a task comment.

        Parameters
        --------------
        task_id: str
            The task id.

        comment_id: str
            The comment id to delete.

        Returns
        -------------
        None
        """
        self.context.upload.delete_comment(
            self.project.org_id, self.project.project_id, task_id, comment_id
        )
