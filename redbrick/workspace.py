"""Interface for interacting with your RedBrick AI Workspaces."""

from typing import Dict, Iterator, List, Optional
from datetime import datetime
from functools import partial

from dateutil import parser  # type: ignore
import tenacity
from tenacity.retry import retry_if_not_exception_type
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_exponential
from redbrick.common.constants import PEERLESS_ERRORS

from redbrick.common.context import RBContext
from redbrick.utils.logging import logger
from redbrick.utils.pagination import PaginationIterator
from redbrick.utils.rb_dicom_utils import dicom_dp_format


class RBWorkspace:
    """Interface for interacting with your RedBrick AI Workspaces."""

    def __init__(self, context: RBContext, org_id: str, workspace_id: str) -> None:
        """Construct RBWorkspace."""
        # pylint: disable=import-outside-toplevel

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
        self.context.workspace.update_datapoint_attributes(
            self.org_id, dp_id, attributes
        )
