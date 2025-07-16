"""Abstract interface to upload."""

from typing import List, Dict, Optional, Any, Sequence, Tuple
from abc import ABC, abstractmethod

import aiohttp

from redbrick.common.constants import MAX_FILE_BATCH_SIZE
from redbrick.common.storage import StorageMethod
from redbrick.types.task import InputTask, OutputTask, CommentPin


class UploadRepo(ABC):
    """Abstract interface to define methods for Upload."""

    @abstractmethod
    def import_dataset_files(
        self,
        org_id: str,
        data_store: str,
        import_name: Optional[str] = None,
        import_id: Optional[str] = None,
        files: Optional[List[Dict]] = None,
    ) -> Tuple[str, List[str]]:
        """Import files into a dataset."""

    @abstractmethod
    def process_dataset_import(
        self,
        org_id: str,
        data_store: str,
        import_id: str,
        total_files: int,
    ) -> bool:
        """Process import."""

    @abstractmethod
    async def create_datapoint_async(  # pylint: disable=too-many-locals
        self,
        aio_client: aiohttp.ClientSession,
        org_id: str,
        workspace_id: Optional[str],
        project_id: Optional[str],
        storage_id: str,
        name: str,
        items: List[str],
        heat_maps: Optional[List[Dict]],
        transforms: Optional[List[Dict]],
        centerlines: Optional[List[Dict]],
        labels_data: Optional[str] = None,
        labels_data_path: Optional[str] = None,
        labels_map: Optional[Sequence[Optional[Dict]]] = None,
        series_info: Optional[List[Dict]] = None,
        meta_data: Optional[Dict] = None,
        is_ground_truth: bool = False,
        pre_assign: Optional[Dict] = None,
        priority: Optional[float] = None,
        attributes: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        Create a datapoint and returns its taskId.

        Name must be unique in the project.
        """

    @abstractmethod
    async def update_items_async(
        self,
        aio_client: aiohttp.ClientSession,
        org_id: str,
        storage_id: str,
        dp_id: Optional[str] = None,
        project_id: Optional[str] = None,
        task_id: Optional[str] = None,
        items: Optional[List[str]] = None,
        series_info: Optional[List[Dict]] = None,
        heat_maps: Optional[List[Dict]] = None,
        transforms: Optional[List[Dict]] = None,
        centerlines: Optional[List[Dict]] = None,
        meta_data: Optional[Dict] = None,
        append: bool = False,
    ) -> Dict:
        """Update items in a datapoint."""

    @abstractmethod
    def items_upload_presign(
        self, org_id: str, project_id: str, files: List[str], file_type: List[str]
    ) -> List[Dict[Any, Any]]:
        """Get a presigned url for uploading items."""

    @abstractmethod
    async def delete_datapoints(
        self, aio_client: aiohttp.ClientSession, org_id: str, dp_ids: List[str]
    ) -> bool:
        """Delete datapoints in a workspace."""

    @abstractmethod
    async def delete_tasks(
        self,
        aio_client: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        task_ids: List[str],
    ) -> bool:
        """Delete tasks in a project."""

    @abstractmethod
    async def delete_tasks_by_name(
        self,
        aio_client: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        task_names: List[str],
    ) -> bool:
        """Delete tasks in a project by task names."""

    @abstractmethod
    async def generate_items_list(
        self,
        aio_client: aiohttp.ClientSession,
        files: List[str],
        import_type: str,
        as_study: bool = False,
        windows: bool = False,
    ) -> str:
        """Generate direct upload items list."""

    @abstractmethod
    async def validate_and_convert_to_import_format(
        self,
        aio_client: aiohttp.ClientSession,
        data: List[InputTask],
        convert: Optional[bool] = None,
        storage_id: Optional[str] = None,
    ) -> Dict:
        """Validate and convert tasks format."""

    @abstractmethod
    def import_tasks_from_workspace(
        self,
        org_id: str,
        project_id: str,
        source_project_id: str,
        task_search: List[Dict],
        with_labels: bool = False,
    ) -> Dict:
        """Import tasks from another project in the same workspace."""

    @abstractmethod
    async def update_priority(
        self,
        session: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        tasks: List[Dict],
    ) -> Optional[str]:
        """Update tasks priorities."""

    @abstractmethod
    async def update_labels(
        self,
        session: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        task_id: str,
        labels_data: Optional[str] = None,
        labels_data_path: Optional[str] = None,
        labels_map: Optional[Sequence[Optional[Dict]]] = None,
        finalize: bool = False,
        time_spent_ms: Optional[int] = None,
        extra_data: Optional[Dict] = None,
    ) -> None:
        """Update tasks labels."""

    @abstractmethod
    async def send_tasks_to_stage(
        self,
        session: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        task_ids: List[str],
        stage_name: str,
    ) -> Optional[str]:
        """Send tasks to different stage."""

    @abstractmethod
    def import_from_dataset(
        self,
        org_id: str,
        dataset_name: str,
        workspace_id: Optional[str],
        project_id: Optional[str],
        import_id: Optional[str],
        series_ids: Optional[List[str]],
        group_by_study: bool,
        is_ground_truth: bool,
    ) -> Optional[str]:
        """Import from dataset."""

    @abstractmethod
    def create_comment(
        self,
        org_id: str,
        project_id: str,
        task_id: str,
        stage_name: str,
        text_comment: str,
        reply_to_comment_id: Optional[str] = None,
        comment_pin: Optional[CommentPin] = None,
        label_id: Optional[str] = None,
    ) -> Optional[Dict]:
        """Create a task comment."""

    @abstractmethod
    def delete_comment(
        self, org_id: str, project_id: str, task_id: str, comment_id: str
    ) -> None:
        """Delete a task comment."""


class DatasetUpload(ABC):
    """
    Primary interface for uploading to a dataset.

    .. code:: python

        >>> dataset = redbrick.get_dataset(api_key="", org_id="", dataset_name="")
        >>> dataset.upload
    """

    @abstractmethod
    def upload_files(
        self,
        path: str,
        import_name: Optional[str] = None,
        concurrency: int = MAX_FILE_BATCH_SIZE,
    ) -> None:
        """Upload files."""


class Upload(ABC):
    """
    Primary interface for uploading to a project.

    .. code:: python

        >>> project = redbrick.get_project(api_key="", org_id="", project_id="")
        >>> project.upload
    """

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
    async def generate_items_list(
        self,
        items_list: List[List[str]],
        import_file_type: str,
        as_study: bool,
        concurrency: int = 50,
    ) -> List[Dict]:
        """Generate items list from local files."""

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
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
