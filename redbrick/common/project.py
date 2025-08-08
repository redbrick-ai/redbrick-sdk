"""Interface for getting basic information about a project."""

from datetime import datetime
from typing import Any, Dict, List, Tuple, Optional
from abc import ABC, abstractmethod

import aiohttp

from redbrick.types.taxonomy import Attribute, ObjectType, Taxonomy


class ProjectRepo(ABC):
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
        sibling_tasks: Optional[int],
        consensus_settings: Optional[Dict[str, Any]] = None,
    ) -> Dict:
        """Create a project and return project_id."""

    @abstractmethod
    def get_org(self, org_id: str) -> Dict:
        """Get organization."""

    @abstractmethod
    def get_projects(self, org_id: str, include_archived: bool = False) -> List[Dict]:
        """Get all projects in organization."""

    @abstractmethod
    def get_taxonomies(
        self, org_id: str, first: int = 50, skip: int = 0
    ) -> List[Taxonomy]:
        """Get a list of taxonomies."""

    @abstractmethod
    async def delete_taxonomy(
        self, session: aiohttp.ClientSession, org_id: str, tax_id: str
    ) -> bool:
        """Delete Taxonomy."""

    @abstractmethod
    def delete_taxonomy_by_name(self, org_id: str, name: str) -> bool:
        """Delete Taxonomy by name."""

    @abstractmethod
    def archive_project(self, org_id: str, project_id: str) -> bool:
        """Archive Project."""

    @abstractmethod
    def unarchive_project(self, org_id: str, project_id: str) -> bool:
        """Unarchive Project."""

    @abstractmethod
    async def delete_project(
        self, session: aiohttp.ClientSession, org_id: str, project_id: str
    ) -> bool:
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
        study_classify: Optional[List[Attribute]],
        series_classify: Optional[List[Attribute]],
        instance_classify: Optional[List[Attribute]],
        object_types: Optional[List[ObjectType]],
    ) -> bool:
        """Create new taxonomy."""

    @abstractmethod
    def get_taxonomy(
        self, org_id: str, tax_id: Optional[str], name: Optional[str]
    ) -> Taxonomy:
        """Get a taxonomy."""

    @abstractmethod
    def update_taxonomy(
        self,
        org_id: str,
        tax_id: str,
        study_classify: Optional[List[Attribute]],
        series_classify: Optional[List[Attribute]],
        instance_classify: Optional[List[Attribute]],
        object_types: Optional[List[ObjectType]],
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
    def update_stage(
        self, org_id: str, project_id: str, stage_name: str, stage_config: Dict
    ) -> Tuple[bool, List[Dict]]:
        """Update project stage."""

    @abstractmethod
    def post_process(self, org_id: str, project_id: str, config: Dict) -> None:
        """Post process trial project."""

    @abstractmethod
    def get_current_user(self) -> Dict:
        """Get current user."""

    @abstractmethod
    def self_health_check(
        self, org_id: str, self_url: str, self_data: Dict
    ) -> Optional[str]:
        """Send a health check update from the model server."""
