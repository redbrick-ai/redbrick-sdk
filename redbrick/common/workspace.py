"""Interface for getting basic information about a workspace."""
from typing import Dict
from abc import ABC, abstractmethod


class WorkspaceRepoInterface(ABC):
    """Abstract interface to Workspace APIs."""

    @abstractmethod
    def get_workspace(self, org_id: str, workspace_id: str) -> Dict:
        """
        Get workspace name and status.

        Raise an exception if workspace does not exist.
        """

    @abstractmethod
    def create_workspace(
        self, org_id: str, workspace_name: str, exists_okay: bool = False
    ) -> Dict:
        """
        Create a workspace.

        Raise an exception if workspace already exists.
        """
