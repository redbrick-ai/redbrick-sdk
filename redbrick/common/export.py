"""Abstract interface to exporting data from a project."""

from typing import Iterator, Optional, List, Dict, Sequence, Tuple, TypedDict
from abc import ABC, abstractmethod
from datetime import datetime

from redbrick.common.constants import MAX_CONCURRENCY
from redbrick.common.enums import ReviewStates, TaskFilters, TaskStates
from redbrick.types.task import OutputTask
from redbrick.types.taxonomy import Taxonomy


class TaskFilterParams(TypedDict, total=False):
    """Task filter query."""

    status: TaskStates
    taskId: str
    userId: Optional[str]
    reviewState: ReviewStates
    recentlyCompleted: bool
    completedAtFrom: str
    completedAtTo: str


class ExportRepo(ABC):
    """Abstract interface to define methods for Export."""

    @abstractmethod
    def get_dataset_imports(
        self, org_id: str, data_store: str
    ) -> Tuple[List[Dict], str]:
        """Get data store imports."""

    @abstractmethod
    def get_dataset_import_series(
        self,
        org_id: str,
        data_store: str,
        search: Optional[str] = None,
        first: int = 20,
        cursor: Optional[str] = None,
    ) -> Tuple[List[Dict[str, str]], str]:
        """Get data store imports."""

    @abstractmethod
    def datapoints_in_project(
        self, org_id: str, project_id: str, stage_name: Optional[str] = None
    ) -> int:
        """Get number of datapoints in project."""

    @abstractmethod
    def get_datapoint_latest(
        self,
        org_id: str,
        project_id: str,
        task_id: str,
        presign_items: bool = False,
        with_consensus: bool = False,
    ) -> Dict:
        """Get the latest datapoint."""

    @abstractmethod
    def get_datapoints_latest(
        self,
        org_id: str,
        project_id: str,
        stage_name: Optional[str] = None,
        cache_time: Optional[datetime] = None,
        presign_items: bool = False,
        with_consensus: bool = False,
        first: int = 50,
        cursor: Optional[str] = None,
    ) -> Tuple[List[Dict], Optional[str], Optional[datetime]]:
        """Get the latest datapoints."""

    @abstractmethod
    def task_search(
        self,
        org_id: str,
        project_id: str,
        stage_name: Optional[str] = None,
        task_search: Optional[str] = None,
        manual_labeling_filters: Optional[TaskFilterParams] = None,
        only_meta_data: bool = True,
        first: int = 50,
        after: Optional[str] = None,
    ) -> Tuple[List[Dict], Optional[str]]:
        """Task search."""

    @abstractmethod
    def presign_items(
        self, org_id: str, storage_id: str, items: Sequence[Optional[str]]
    ) -> List[Optional[str]]:
        """Presign download items."""

    @abstractmethod
    def task_events(
        self,
        org_id: str,
        project_id: str,
        task_id: Optional[str] = None,
        stage_name: Optional[str] = None,
        cache_time: Optional[datetime] = None,
        with_labels: bool = False,
        first: int = 10,
        after: Optional[str] = None,
    ) -> Tuple[List[Dict], Optional[str]]:
        """Get task events."""

    @abstractmethod
    def active_time(
        self,
        org_id: str,
        project_id: str,
        stage_name: str,
        task_id: Optional[str] = None,
        first: int = 100,
        after: Optional[str] = None,
    ) -> Tuple[List[Dict], Optional[str]]:
        """Get task active time."""


class DatasetExport(ABC):
    """
    Primary interface for various export methods.

    The export module has many functions for exporting annotations and meta-data from datasets. The export module is available from the :attr:`redbrick.RBProject` module.

    .. code:: python

        >>> dataset = redbrick.get_dataset(api_key="", org_id="", dataset_name="")
        >>> dataset.export # Export
    """

    @abstractmethod
    def get_data_store_series(
        self, *, search: Optional[str] = None, page_size: int = MAX_CONCURRENCY
    ) -> Iterator[Dict[str, str]]:
        """Get data store series."""

    @abstractmethod
    def export_to_files(
        self,
        path: str,
        page_size: int = MAX_CONCURRENCY,
        number: Optional[int] = None,
        search: Optional[str] = None,  # pylint: disable=unused-argument
    ) -> None:
        """Export dataset to folder.

        Args
        ----
        dataset_name: str
            Name of the dataset.
        path: str
            Path to the folder where the dataset will be saved.
        page_size: int
            Number of series to export in parallel.
        number: int
            Number of series to export in total.
        search: str
            Search string to filter the series to export.
        """


class Export(ABC):
    """
    Primary interface for various export methods.

    The export module has many functions for exporting annotations and meta-data from projects. The export module is available from the :attr:`redbrick.RBProject` module.

    .. code:: python

        >>> project = redbrick.get_project(api_key="", org_id="", project_id="")
        >>> project.export # Export
    """

    @abstractmethod
    def get_raw_data_latest(
        self,
        concurrency: int,
        stage_name: Optional[str] = None,
        from_timestamp: Optional[float] = None,
        presign_items: bool = False,
        with_consensus: bool = False,
        task_id: Optional[str] = None,
    ) -> Iterator[Dict]:
        """Get raw task data."""

    @abstractmethod
    def preprocess_export(
        self, taxonomy: Taxonomy, get_color_map: bool
    ) -> Tuple[Dict, Dict]:
        """Get classMap and colorMap."""

    @abstractmethod
    async def export_nifti_label_data(  # pylint: disable=too-many-locals
        self,
        datapoint: Dict,
        taxonomy: Taxonomy,
        task_file: Optional[str],
        image_dir: Optional[str],
        segmentation_dir: Optional[str],
        semantic_mask: bool,
        binary_mask: Optional[bool],
        old_format: bool,
        no_consensus: bool,
        color_map: Dict,
        dicom_to_nifti: bool,
        png_mask: bool,
        rt_struct: bool,
        mhd_mask: bool,
        get_task: bool,
    ) -> Optional[OutputTask]:
        """Export nifti label maps."""

    @abstractmethod
    def export_tasks(  # pylint: disable=too-many-locals
        self,
        *,
        concurrency: int = 10,
        only_ground_truth: bool = False,
        stage_name: Optional[str] = None,
        task_id: Optional[str] = None,
        from_timestamp: Optional[float] = None,
        old_format: bool = False,
        without_masks: bool = False,
        without_json: bool = False,
        semantic_mask: bool = False,
        binary_mask: Optional[bool] = None,
        no_consensus: Optional[bool] = None,
        with_files: bool = False,
        dicom_to_nifti: bool = False,
        png: bool = False,
        rt_struct: bool = False,
        mhd: bool = False,
        destination: Optional[str] = None,
    ) -> Iterator[OutputTask]:
        """Export annotation data.

        Meta-data and category information returned as an Object. Segmentations are written to
        your disk in NIfTI-1 format. Please `visit our
        documentation <https://sdk.redbrickai.com/formats/index.html#export>`_
        for more information on the format.

        >>> project = redbrick.get_project(org_id, project_id, api_key, url)
        >>> project.export.export_tasks()

        Parameters
        -----------
        concurrency: int = 10

        only_ground_truth: bool = False
            If set to True, will only return data that has
            been completed in your workflow. If False, will
            export latest state.

        stage_name: Optional[str] = None
            If set, will only export tasks that are currently
            in the given stage.

        task_id: Optional[str] = None
            If the unique task_id is mentioned, only a single
            datapoint will be exported.

        from_timestamp: Optional[float] = None
            If the timestamp is mentioned, will only export tasks
            that were labeled/updated since the given timestamp.
            Format - output from datetime.timestamp()

        old_format: bool = False
            Whether to export tasks in old format.

        without_masks: bool = False
            Exports only tasks JSON without downloading any segmentation masks.
            Note: This is not recommended for tasks with overlapping labels.

        without_json: bool = False
            Doesn't create the tasks JSON file.

        semantic_mask: bool = False
            Whether to export all segmentations as semantic_mask.
            This will create one instance per class.
            If this is set to True and a task has multiple instances per class,
            then attributes belonging to each instance will not be exported.

        binary_mask: Optional[bool] = None
            Whether to export all segmentations as binary masks.
            This will create one segmentation file per instance.
            If this is set to None and a task has overlapping labels,
            then binary_mask option will be True for that particular task.

        no_consensus: Optional[bool] = None
            Whether to export tasks without consensus info.
            If None, will default to export with consensus info,
            if it is enabled for the given project.
            (Applicable only for new format export)

        with_files: bool = False
            Export with files (e.g. images/video frames)

        dicom_to_nifti: bool = False
            Convert DICOM images to NIfTI. Applicable when `with_files` is True.

        png: bool = False
            Export labels as PNG masks.

        rt_struct: bool = False
            Export labels as DICOM RT-Struct. (Only for DICOM images)

        mhd: bool = False
            Export segmentation masks in MHD format.

        destination: Optional[str] = None
            Destination directory (Default: current directory)

        Returns
        -----------
        Iterator[:obj:`~redbrick.types.task.OutputTask`]
            Datapoint and labels in RedBrick AI format. See
            https://sdk.redbrickai.com/formats/index.html#export


        .. note:: If both `semantic_mask` and `binary_mask` options are True,
            then one binary mask will be generated per class.
        """

    @abstractmethod
    def list_tasks(
        self,
        search: TaskFilters = TaskFilters.ALL,
        concurrency: int = 10,
        limit: Optional[int] = 50,
        *,
        stage_name: Optional[str] = None,
        user_id: Optional[str] = None,
        task_id: Optional[str] = None,
        task_name: Optional[str] = None,
        exact_match: bool = False,
        completed_at: Optional[Tuple[Optional[float], Optional[float]]] = None,
    ) -> Iterator[Dict]:
        """
        Search tasks based on multiple queries for a project.
        This function returns minimal meta-data about the queried tasks.

        >>> project = redbrick.get_project(org_id, project_id, api_key, url)
        >>> result = project.export.list_tasks()

        Parameters
        -----------
        search: :obj:`~redbrick.common.enums.TaskFilters` = TaskFilters.ALL
            Task filter type.

        concurrency: int = 10
            The number of requests that will be made in parallel.

        limit: Optional[int] = 50
            The number of tasks to return.
            Use None to return all tasks matching the search query.

        stage_name: Optional[str] = None
            If present, will return tasks that are:
                a. Available in stage_name: If search == TaskFilters.QUEUED
                b. Completed in stage_name: If search == TaskFilters.COMPLETED

        user_id: Optional[str] = None
            User id/email. If present, will return tasks that are:
                a. Assigned to user_id: If search == TaskFilters.QUEUED
                b. Completed by user_id: If search == TaskFilters.COMPLETED

        task_id: Optional[str] = None
            If present, will return data for the given task id.

        task_name: Optional[str] = None
            If present, will return data for the given task name.
            This will do a prefix search with the given task name.

        exact_match: bool = False
            Applicable when searching for tasks by task_name.
            If True, will do a full match instead of partial match.

        completed_at: Optional[Tuple[Optional[float], Optional[float]]] = None
            If present, will return tasks that were completed in the given time range.
            The tuple contains the `from` and `to` timestamps respectively.

        Returns
        -----------
        Iterator[Dict]
            >>> [{
                "taskId": str,
                "name": str,
                "createdAt": str,
                "storageId": str,
                "updatedAt": str,
                "currentStageName": str,
                "createdBy"?: {"userId": str, "email": str},
                "priority"?: float([0, 1]),
                "metaData"?: dict,
                "series"?: [{"name"?: str, "metaData"?: dict}],
                "assignees"?: [{
                    "user": str,
                    "status": TaskStates,
                    "assignedAt": datetime,
                    "lastSavedAt"?: datetime,
                    "completedAt"?: datetime,
                    "timeSpentMs"?: float,
                }]
            }]
        """

    @abstractmethod
    def get_task_events(
        self,
        *,
        task_id: Optional[str] = None,
        only_ground_truth: bool = True,
        concurrency: int = 10,
        from_timestamp: Optional[float] = None,
        with_labels: bool = False,
    ) -> Iterator[Dict]:
        """Generate an audit log of all actions performed on tasks.

        Use this method to get a detailed summary of all the actions performed on your
        tasks, including:

        - Who uploaded the data
        - Who annotated your tasks
        - Who reviewed your tasks
        - and more.

        This can be particulary useful to present to auditors who are interested in your
        quality control workflows.

        Parameters
        -----------
        task_id: Optional[str] = None
            If set, returns events only for the given task.

        only_ground_truth: bool = True
            If set to True, will return events for tasks
            that have been completed in your workflow.

        concurrency: int = 10
            The number of requests that will be made in parallel.

        from_timestamp: Optional[float] = None
            If the timestamp is mentioned, will only export tasks
            that were labeled/updated since the given timestamp.
            Format - output from datetime.timestamp()

        with_labels: bool = False
            Get metadata of labels submitted in each stage.

        Returns
        -----------
        Iterator[Dict]
            >>> [{
                "taskId": str,
                "currentStageName": str,
                "events": List[Dict]
            }]
        """

    @abstractmethod
    def get_active_time(
        self,
        *,
        stage_name: str,
        task_id: Optional[str] = None,
        concurrency: int = 100,
    ) -> Iterator[Dict]:
        """Get active time spent on tasks for labeling/reviewing.

        Parameters
        -----------
        stage_name: str
            Stage for which to return the time info.

        task_id: Optional[str] = None
            If set, will return info for the given task in the given stage.

        concurrency: int = 100
            Request batch size.

        Returns
        -----------
        Iterator[Dict]
            >>> [{
                "orgId": string,
                "projectId": string,
                "stageName": string,
                "taskId": string,
                "completedBy": string,
                "timeSpent": number,  # In milliseconds
                "completedAt": datetime,
                "cycle": number  # Task cycle
            }]
        """
