"""Interface for getting basic information about a project."""
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from abc import ABC, abstractmethod


class ProjectRepoInterface(ABC):
    """Abstract interface to Project APIs."""

    @abstractmethod
    def get_project(self, org_id: str, project_id: str) -> Dict:
        """
        Get project name and status.

        Raise an exception if project does not exist.
        """

    @abstractmethod
    def get_stages(self, org_id: str, project_id: str) -> List[Dict]:
        """Get stages."""

    @abstractmethod
    def create_project(
        self,
        org_id: str,
        name: str,
        stages: List[dict],
        td_type: str,
        tax_name: str,
        workspace_id: Optional[str],
    ) -> Dict:
        """Create a project and return project_id."""

    @abstractmethod
    def get_org(self, org_id: str) -> Dict:
        """Get organization."""

    @abstractmethod
    def get_projects(self, org_id: str) -> List[Dict]:
        """Get all projects in organization."""

    @abstractmethod
    def get_taxonomies(self, org_id: str) -> List[Dict]:
        """Get a list of taxonomies."""

    @abstractmethod
    def delete_project(self, org_id: str, project_id: str) -> None:
        """Delete Project."""

    @abstractmethod
    def get_labeling_information(
        self,
        org_id: str,
        start_date: datetime,
        end_date: datetime,
        first: int,
        cursor: Optional[str] = None,
    ) -> Tuple[List[Dict], Optional[str]]:
        """Get org labeling information."""

    @abstractmethod
    def create_taxonomy(
        self,
        org_id: str,
        name: str,
        categories: List[Dict],
        attributes: Optional[List[Dict]],
        task_categories: Optional[List[Dict]],
        task_attributes: Optional[List[Dict]],
    ) -> bool:
        """Create taxonomy."""

    @abstractmethod
    def create_taxonomy_new(
        self,
        org_id: str,
        name: str,
        study_classify: Optional[List[Dict]],
        series_classify: Optional[List[Dict]],
        instance_classify: Optional[List[Dict]],
        object_types: Optional[List[Dict]],
    ) -> bool:
        """Create new taxonomy."""

    @abstractmethod
    def get_taxonomy(
        self, org_id: str, tax_id: Optional[str], name: Optional[str]
    ) -> Dict:
        """Get a taxonomy."""

    @abstractmethod
    def update_taxonomy(
        self,
        org_id: str,
        tax_id: str,
        study_classify: Optional[List[Dict]],
        series_classify: Optional[List[Dict]],
        instance_classify: Optional[List[Dict]],
        object_types: Optional[List[Dict]],
    ) -> bool:
        """Update taxonomy."""

    @abstractmethod
    def get_label_storage(self, org_id: str, project_id: str) -> Tuple[str, str]:
        """Get label storage method for a project."""

    @abstractmethod
    def set_label_storage(
        self, org_id: str, project_id: str, storage_id: str, path: str
    ) -> bool:
        """Set label storage method for a project."""

    @abstractmethod
    def get_current_user(self) -> Dict:
        """Get current user."""

    @abstractmethod
    def get_members(self, org_id: str, project_id: str) -> List[Dict]:
        """Get members of a project."""
