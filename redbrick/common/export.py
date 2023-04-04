"""Abstract interface to exporting data from a project."""

from typing import Optional, List, Dict, Sequence, Tuple, TypedDict
from abc import ABC, abstractmethod
from datetime import datetime

import aiohttp

from redbrick.common.enums import ReviewStates, TaskStates


class TaskFilterParams(TypedDict, total=False):
    """Task filter query."""

    status: TaskStates
    taskId: str
    userId: Optional[str]
    reviewState: ReviewStates
    benchmark: bool
    recentlyCompleted: bool


class ExportControllerInterface(ABC):
    """Abstract interface to define methods for Export."""

    @abstractmethod
    def datapoints_in_project(
        self, org_id: str, project_id: str, stage_name: Optional[str] = None
    ) -> int:
        """Get number of datapoints in project."""

    @abstractmethod
    def get_datapoint_latest(
        self,
        org_id: str,
        project_id: str,
        task_id: str,
        presign_items: bool = False,
        with_consensus: bool = False,
    ) -> Dict:
        """Get the latest datapoint."""

    @abstractmethod
    def get_datapoints_latest(
        self,
        org_id: str,
        project_id: str,
        stage_name: Optional[str] = None,
        cache_time: Optional[datetime] = None,
        presign_items: bool = False,
        with_consensus: bool = False,
        first: int = 50,
        cursor: Optional[str] = None,
    ) -> Tuple[List[Dict], Optional[str], Optional[datetime]]:
        """Get the latest datapoints."""

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
        manual_labeling_filters: Optional[TaskFilterParams] = None,
        only_meta_data: bool = True,
        first: int = 50,
        after: Optional[str] = None,
    ) -> Tuple[List[Dict], Optional[str]]:
        """Task search."""

    @abstractmethod
    def presign_items(
        self, org_id: str, storage_id: str, items: Sequence[Optional[str]]
    ) -> List[Optional[str]]:
        """Presign download items."""

    @abstractmethod
    def task_events(
        self,
        org_id: str,
        project_id: str,
        stage_name: Optional[str] = None,
        cache_time: Optional[datetime] = None,
        first: int = 10,
        after: Optional[str] = None,
    ) -> Tuple[List[Dict], Optional[str]]:
        """Get task events."""
