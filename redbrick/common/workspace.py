"""Interface for getting basic information about a workspace."""

from typing import Dict, List, Optional, Tuple
from abc import ABC, abstractmethod


class WorkspaceRepo(ABC):
    """Abstract interface to Workspace APIs."""

    @abstractmethod
    def get_workspaces(self, org_id: str) -> List[Dict]:
        """Get list of workspaces."""

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

    @abstractmethod
    def update_schema(
        self,
        org_id: str,
        workspace_id: str,
        metadata_schema: Optional[List[Dict]],
        classification_schema: Optional[List[Dict]],
    ) -> None:
        """Update workspace metadata and classification schema."""

    @abstractmethod
    def update_cohorts(
        self, org_id: str, workspace_id: str, cohorts: List[Dict]
    ) -> None:
        """Update workspace cohorts."""

    @abstractmethod
    def get_datapoints(
        self,
        org_id: str,
        workspace_id: str,
        first: int = 50,
        after: Optional[str] = None,
    ) -> Tuple[List[Dict], Optional[str]]:
        """Get datapoints for a workspace."""

    @abstractmethod
    def toggle_datapoints_archived_status(
        self, org_id: str, dp_ids: List[str], archived: bool
    ) -> None:
        """Toggle archived status for datapoints."""

    @abstractmethod
    def toggle_datapoints_cohorts(
        self,
        org_id: str,
        workspace_id: str,
        cohort_name: str,
        dp_ids: List[str],
        include: bool,
    ) -> None:
        """Toggle cohort membership for workspace datapoints."""

    @abstractmethod
    def update_datapoint_attributes(
        self, org_id: str, dp_id: str, attributes: List[Dict]
    ) -> None:
        """Update datapoint attributes."""

    @abstractmethod
    def add_datapoints_to_projects(
        self,
        org_id: str,
        workspace_id: str,
        project_ids: List[str],
        dp_ids: List[str],
        ground_truth: bool,
    ) -> None:
        """Add datapoints to project."""
