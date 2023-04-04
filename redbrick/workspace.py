"""Interface for interacting with your RedBrick AI Workspaces."""
from typing import Dict
from datetime import datetime
from dateutil import parser  # type: ignore

import tenacity
from tenacity.retry import retry_if_not_exception_type
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_exponential
from redbrick.common.constants import PEERLESS_ERRORS

from redbrick.common.context import RBContext
from redbrick.utils.logging import logger


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

    def __wait_for_workspace_to_finish_creating(self) -> Dict:
        project = {}
        try:
            for attempt in tenacity.Retrying(
                reraise=True,
                stop=stop_after_attempt(10),
                wait=wait_exponential(multiplier=1, min=1, max=10),
                retry=retry_if_not_exception_type(PEERLESS_ERRORS),
            ):
                with attempt:
                    project = self.context.workspace.get_workspace(
                        self.org_id, self.workspace_id
                    )
                    if project["status"] == "CREATING":
                        if attempt.retry_state.attempt_number == 1:
                            logger.info("Project is still creating...")
                        raise Exception("Unknown problem occurred")
        except tenacity.RetryError as error:
            raise Exception("Unknown problem occurred") from error

        if project["status"] == "REMOVING":
            raise Exception("Project has been deleted")
        if project["status"] == "CREATION_FAILURE":
            raise Exception("Project failed to be created")
        if project["status"] == "CREATION_SUCCESS":
            return project
        raise Exception("Unknown problem occurred")

    def _get_workspace(self) -> None:
        """Get project to confirm it exists."""
        project = self.__wait_for_workspace_to_finish_creating()

        self._workspace_name = project["name"]
        self._created_at = parser.parse(project["createdAt"])

    def __str__(self) -> str:
        """Get string representation of RBProject object."""
        return f"RedBrick Workspace - {self.name} - id:( {self.workspace_id} )"

    def __repr__(self) -> str:
        """Representation of object."""
        return str(self)
