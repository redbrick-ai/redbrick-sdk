"""Interface for getting basic information about a project."""

from typing import Dict, List
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
        self, org_id: str, name: str, stages: List[dict], td_type: str, tax_name: str
    ) -> Dict:
        """Create a project and return project_id."""

    @abstractmethod
    def get_org(self, org_id: str) -> Dict:
        """Get organization."""

    @abstractmethod
    def get_projects(self, org_id: str) -> List[Dict]:
        """Get all projects in organization."""

    @abstractmethod
    def get_taxonomies(self, org_id: str) -> List[str]:
        """Get a list of taxonomies."""
