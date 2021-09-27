"""Abstract interface to exporting data from a project."""

from typing import Optional, List, Dict, Tuple
from abc import ABC, abstractmethod


class ExportControllerInterface(ABC):
    @abstractmethod
    def get_datapoints_input(
        self,
        org_id: str,
        project_id: str,
        first: int = 50,
        presign: bool = False,
        cursor: Optional[str] = None,
    ) -> Tuple[List[Dict], Optional[str]]:
        """Get datapoints that were uploaded to the project."""

    @abstractmethod
    def get_output_info(self, org_id: str, project_id: str,) -> Dict:
        """Get info about the output labelset and taxonomy."""

    @abstractmethod
    def get_datapoints_output(
        self,
        org_id: str,
        project_id: str,
        first: int = 50,
        presign: bool = False,
        cursor: Optional[str] = None,
    ) -> Tuple[List[Dict], Optional[str]]:
        """Get datapoints that have made it to the output of the project."""

    @abstractmethod
    def datapoints_in_project(self, org_id: str, project_id: str) -> int:
        """Get number of datapoints in project."""

    @abstractmethod
    def get_datapoints_latest(
        self,
        org_id: str,
        project_id: str,
        first: int = 50,
        presign: bool = False,
        cursor: Optional[str] = None,
    ) -> Tuple[List[Dict], Optional[str]]:
        """Get the latest datapoints."""

    @abstractmethod
    def get_datapoint_latest(self, org_id: str, project_id: str, task_id: str) -> Dict:
        """Get the latest labels for a single datapoint."""
