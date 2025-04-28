"""Interface for interacting with your RedBrick AI Workspaces."""

import asyncio
from typing import Dict, Iterator, List, Optional
from datetime import datetime
from functools import partial

from dateutil import parser  # type: ignore
import tenacity
from tenacity.retry import retry_if_not_exception_type
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_exponential
from redbrick.common.constants import PEERLESS_ERRORS

from redbrick.common.entities import RBWorkspace
from redbrick.common.context import RBContext
from redbrick.types.task import InputTask
from redbrick.upload.interact import upload_datapoints
from redbrick.utils.async_utils import gather_with_concurrency, get_session
from redbrick.utils.logging import log_error, logger
from redbrick.utils.pagination import PaginationIterator
from redbrick.utils.rb_dicom_utils import dicom_dp_format


class RBWorkspaceImpl(RBWorkspace):
    """Interface for interacting with your RedBrick AI Workspaces."""

    def __init__(self, context: RBContext, org_id: str, workspace_id: str) -> None:
        """Construct RBWorkspace."""
        self.context = context

        self._org_id = org_id
        self._workspace_id = workspace_id
        self._workspace_name: str
        self._taxonomy_name: str
        self._created_at: datetime
        self._metadata_schema: List[Dict] = []
        self._classification_schema: List[Dict] = []
        self._cohorts: List[Dict] = []

        # check if workspace exists on backend to validate
        self._get_workspace()

    @property
    def org_id(self) -> str:
        """
        Read only property.

        Retrieves the unique Organization UUID that this workspace belongs to
        """
        return self._org_id

    @property
    def workspace_id(self) -> str:
        """
        Read only property.

        Retrieves the unique Workspace ID UUID.
        """
        return self._workspace_id

    @property
    def name(self) -> str:
        """
        Read only name property.

        Retrieves the workspace name.
        """
        return self._workspace_name

    @property
    def metadata_schema(self) -> List[Dict]:
        """Retrieves the workspace metadata schema."""
        return self._metadata_schema

    @property
    def classification_schema(self) -> List[Dict]:
        """Retrieves the workspace classification schema."""
        return self._classification_schema

    @property
    def cohorts(self) -> List[Dict]:
        """Retrieves the workspace cohorts."""
        return self._cohorts

    def __wait_for_workspace_to_finish_creating(self) -> Dict:
        workspace = {}
        try:
            for attempt in tenacity.Retrying(
                reraise=True,
                stop=stop_after_attempt(10),
                wait=wait_exponential(multiplier=1, min=1, max=10),
                retry=retry_if_not_exception_type(PEERLESS_ERRORS),
            ):
                with attempt:
                    workspace = self.context.workspace.get_workspace(
                        self.org_id, self.workspace_id
                    )
                    if workspace["status"] == "CREATING":
                        if attempt.retry_state.attempt_number == 1:
                            logger.info("Project is still creating...")
                        raise Exception("Unknown problem occurred")
        except tenacity.RetryError as error:
            raise Exception("Unknown problem occurred") from error

        if workspace["status"] == "REMOVING":
            raise Exception("Project has been deleted")
        if workspace["status"] == "CREATION_FAILURE":
            raise Exception("Project failed to be created")
        if workspace["status"] == "CREATION_SUCCESS":
            return workspace
        raise Exception("Unknown problem occurred")

    def _get_workspace(self) -> None:
        """Get workspace to confirm it exists."""
        workspace = self.__wait_for_workspace_to_finish_creating()

        self._workspace_name = workspace["name"]
        self._created_at = parser.parse(workspace["createdAt"])
        if workspace.get("metadataSchema"):
            self._metadata_schema = workspace["metadataSchema"]
        if workspace.get("classificationSchema"):
            self._classification_schema = workspace["classificationSchema"]
        if workspace.get("cohorts"):
            self._cohorts = workspace["cohorts"]

    def __str__(self) -> str:
        """Get string representation of RBWorkspace object."""
        return f"RedBrick Workspace - {self.name} - id:( {self.workspace_id} )"

    def __repr__(self) -> str:
        """Representation of object."""
        return str(self)

    def update_schema(
        self,
        metadata_schema: Optional[List[Dict]] = None,
        classification_schema: Optional[List[Dict]] = None,
    ) -> None:
        """Update workspace metadata and classification schema."""
        self.context.workspace.update_schema(
            self.org_id, self.workspace_id, metadata_schema, classification_schema
        )

    def update_cohorts(self, cohorts: List[Dict]) -> None:
        """Update workspace cohorts."""
        self.context.workspace.update_cohorts(self.org_id, self.workspace_id, cohorts)

    def get_datapoints(
        self,
        *,
        concurrency: int = 10,
    ) -> Iterator[Dict]:
        """Get datapoints in a workspace."""
        my_iter = PaginationIterator(
            partial(  # type: ignore
                self.context.workspace.get_datapoints, self.org_id, self.workspace_id
            ),
            concurrency,
        )

        for val in my_iter:
            yield dicom_dp_format(val)

    def archive_datapoints(self, dp_ids: List[str]) -> None:
        """Archive datapoints."""
        self.context.workspace.toggle_datapoints_archived_status(
            self.org_id, dp_ids, True
        )

    def unarchive_datapoints(self, dp_ids: List[str]) -> None:
        """Unarchive datapoints."""
        self.context.workspace.toggle_datapoints_archived_status(
            self.org_id, dp_ids, False
        )

    def add_datapoints_to_cohort(self, cohort_name: str, dp_ids: List[str]) -> None:
        """Add datapoints to a cohort."""
        self.context.workspace.toggle_datapoints_cohorts(
            self.org_id, self.workspace_id, cohort_name, dp_ids, True
        )

    def remove_datapoints_from_cohort(
        self, cohort_name: str, dp_ids: List[str]
    ) -> None:
        """Remove datapoints from a cohort."""
        self.context.workspace.toggle_datapoints_cohorts(
            self.org_id, self.workspace_id, cohort_name, dp_ids, False
        )

    def update_datapoint_attributes(self, dp_id: str, attributes: Dict) -> None:
        """Update datapoint attributes."""
        attrs: List[Dict] = []
        for key, value in attributes.items():
            attr: Dict = {}
            if isinstance(key, int):
                attr["attrid"] = key
            else:
                attr["name"] = key

            if (not isinstance(value, bool) and isinstance(value, int)) or (
                isinstance(value, list) and all(isinstance(val, int) for val in value)
            ):
                attr["optionid"] = value
            else:
                attr["value"] = value
            attrs.append(attr)

        self.context.workspace.update_datapoint_attributes(self.org_id, dp_id, attrs)

    def add_datapoints_to_projects(
        self, project_ids: List[str], dp_ids: List[str], is_ground_truth: bool = False
    ) -> None:
        """Add datapoints to project.

        Parameters
        --------------
        project_ids: List[str]
            The projects in which you'd like to add the given datapoints.

        dp_ids: List[str]
            List of datapoints that need to be added to projects.

        is_ground_truth: bool = False
            Whether to create tasks directly in ground truth stage.
        """
        self.context.workspace.add_datapoints_to_projects(
            self.org_id, self.workspace_id, project_ids, dp_ids, is_ground_truth
        )

    def create_datapoints(
        self,
        storage_id: str,
        points: List[InputTask],
        *,
        concurrency: int = 50,
    ) -> List[Dict]:
        """
        Create datapoints in workspace.

        Upload data to your workspace (without annotations). Please visit
        `our documentation <https://sdk.redbrickai.com/formats/index.html#import>`_
        to understand the format for ``points``.

        .. code:: python

            workspace = redbrick.get_workspace(org_id, workspace_id, api_key, url)
            points = [
                {
                    "name": "...",
                    "series": [
                        {
                            "items": "...",
                        }
                    ]
                }
            ]
            workspace.create_datapoints(storage_id, points)


        Parameters
        --------------
        storage_id: str
            Your RedBrick AI external storage_id. This can be found under the Storage Tab
            on the RedBrick AI platform. To directly upload images to rbai,
            use redbrick.StorageMethod.REDBRICK.

        points: List[:obj:`~redbrick.types.task.InputTask`]
            Please see the RedBrick AI reference documentation for overview of the format.
            https://sdk.redbrickai.com/formats/index.html#import.
            Fields with `annotation` information are not supported in workspace.

        concurrency: int = 50

        Returns
        -------------
        List[Dict]
            List of datapoint objects with key `response` if successful, else `error`

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
            org_id=self.org_id,
            workspace_id=self.workspace_id,
            project_id=None,
            taxonomy=None,
            storage_id=storage_id,
            points=points,
            is_ground_truth=False,
            segmentation_mapping={},
            concurrency=concurrency,
        )

    async def _update_datapoints_metadata(
        self, storage_id: str, points: List[Dict]
    ) -> None:
        async with get_session() as session:
            await gather_with_concurrency(
                10,
                *[
                    self.context.upload.update_items_async(
                        aio_client=session,
                        org_id=self.org_id,
                        storage_id=storage_id,
                        dp_id=point["dpId"],
                        meta_data=point.get("metaData"),
                    )
                    for point in points
                ],
                progress_bar_name="Updating datapoints metadata",
                keep_progress_bar=True,
            )

    def update_datapoints_metadata(self, storage_id: str, points: List[Dict]) -> None:
        """Update datapoints metadata.

        Update metadata for datapoints in workspace.

        .. code:: python

            workspace = redbrick.get_workspace(org_id, workspace_id, api_key, url)
            points = [
                {
                    "dpId": "...",
                    "metaData": {
                        "property": "value",
                    }
                }
            ]
            workspace.update_datapoints_metadata(storage_id, points)


        Parameters
        --------------
        storage_id: str
            Storage method where the datapoints are stored.

        points: List[:obj:`~redbrick.types.task.InputTask`]
            List of datapoints with dpId and metaData values.
        """
        asyncio.run(self._update_datapoints_metadata(storage_id, points))

    async def _delete_datapoints(self, dp_ids: List[str], concurrency: int) -> bool:
        async with get_session() as session:
            coros = [
                self.context.upload.delete_datapoints(
                    session,
                    self.org_id,
                    dp_ids[batch : batch + concurrency],
                )
                for batch in range(0, len(dp_ids), concurrency)
            ]
            success = await gather_with_concurrency(
                10,
                *coros,
                progress_bar_name="Deleting datapoints",
                keep_progress_bar=True,
            )

        return all(success)

    def delete_datapoints(self, dp_ids: List[str], concurrency: int = 50) -> bool:
        """Delete workspace datapoints based on ids.

        >>> workspace = redbrick.get_workspace(org_id, workspace_id, api_key, url)
        >>> workspace.delete_datapoints([...])

        Parameters
        --------------
        dp_ids: List[str]
            List of datapoint ids to delete.

        concurrency: int = 50
            The number of datapoints to delete at a time.
            We recommend keeping this less than or equal to 50.

        Returns
        -------------
        bool
            True if successful, else False.
        """
        concurrency = min(concurrency, 50)
        return asyncio.run(self._delete_datapoints(dp_ids, concurrency))

    def import_from_dataset(
        self,
        dataset_name: str,
        *,
        import_id: Optional[str] = None,
        series_ids: Optional[List[str]] = None,
        group_by_study: bool = False,
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
        """
        error = self.context.upload.import_from_dataset(
            self.org_id,
            dataset_name,
            self.workspace_id,
            None,
            import_id,
            series_ids,
            group_by_study,
            False,
        )
        if error:
            log_error(error)
