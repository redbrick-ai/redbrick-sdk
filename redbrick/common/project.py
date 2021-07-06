"""Interface for getting basic information about a project."""

from typing import Dict, List
from abc import ABC, abstractmethod


class ProjectRepoInterface(ABC):
    """Abstract interface to Project APIs."""

    @abstractmethod
    def get_project_name(self, org_id: str, project_id: str) -> str:
        """
        Get project name.

        Raise an exception if project does not exist.
        """

    @abstractmethod
    def get_stages(self, org_id: str, project_id: str) -> List[Dict]:
        """Get stages."""
