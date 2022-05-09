"""Abstract interface to exporting data from a project."""

from typing import Optional, List, Dict, Tuple
from abc import ABC, abstractmethod
from datetime import datetime

import aiohttp


class ExportControllerInterface(ABC):
    """Abstract interface to define methods for Export."""

    @abstractmethod
    def get_output_info(
        self,
        org_id: str,
        project_id: str,
    ) -> Dict:
        """Get info about the output labelset and taxonomy."""

    @abstractmethod
    def get_datapoints_output(
        self,
        org_id: str,
        project_id: str,
        first: int = 50,
        cursor: Optional[str] = None,
    ) -> Tuple[List[Dict], Optional[str]]:
        """Get datapoints that have made it to the output of the project."""

    @abstractmethod
    def datapoints_in_project(
        self, org_id: str, project_id: str, stage_name: Optional[str] = None
    ) -> int:
        """Get number of datapoints in project."""

    @abstractmethod
    def get_datapoints_latest(
        self,
        org_id: str,
        project_id: str,
        stage_name: Optional[str] = None,
        cache_time: Optional[datetime] = None,
        first: int = 50,
        cursor: Optional[str] = None,
    ) -> Tuple[List[Dict], Optional[str], Optional[datetime]]:
        """Get the latest datapoints."""

    @abstractmethod
    def get_datapoint_latest(self, org_id: str, project_id: str, task_id: str) -> Dict:
        """Get the latest labels for a single datapoint."""

    @abstractmethod
    async def get_labels(
        self, session: aiohttp.ClientSession, org_id: str, project_id: str, dp_id: str
    ) -> Dict:
        """Get input labels."""

    @abstractmethod
    def task_search(
        self,
        org_id: str,
        project_id: str,
        stage_name: Optional[str] = None,
        task_search: Optional[str] = None,
        first: int = 50,
        after: Optional[str] = None,
    ) -> Tuple[List[Dict], Optional[str]]:
        """Task search."""

    @abstractmethod
    def presign_items(
        self, org_id: str, storage_id: str, items: List[str]
    ) -> List[str]:
        """Presign download items."""
