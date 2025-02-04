"""Abstract interface to exporting."""

from typing import Optional, List, Dict, Tuple
from abc import ABC, abstractmethod
import aiohttp


class LabelingControllerInterface(ABC):
    """Abstract interface to Labeling APIs."""

    @abstractmethod
    async def presign_labels_path(
        self,
        session: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        task_id: str,
        version_id: str,
        data_count: int,
        seg_count: int,
    ) -> Tuple[List[Dict], List[Dict]]:
        """Presign labels path."""

    @abstractmethod
    async def put_labeling_results(
        self,
        session: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        stage_name: str,
        task_id: str,
        labels_data: Optional[str] = None,
        labels_data_path: Optional[str] = None,
        labels_map: Optional[List[Dict]] = None,
        finished: bool = True,
    ) -> None:
        """Put Labeling results."""

    @abstractmethod
    async def put_labeling_task_result(
        self,
        session: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        stage_name: str,
        task_id: str,
    ) -> None:
        """Put labeling result for task."""

    @abstractmethod
    async def put_review_task_result(
        self,
        session: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        stage_name: str,
        task_id: str,
        review_val: bool,
    ) -> None:
        """Put review result for task."""

    @abstractmethod
    def assign_tasks(
        self,
        org_id: str,
        project_id: str,
        task_ids: List[str],
        emails: Optional[List[str]] = None,
        current_user: bool = False,
        refresh: bool = True,
    ) -> List[Dict]:
        """Assign tasks to specified email or current API key."""

    @abstractmethod
    async def move_task_to_start(
        self,
        session: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        task_id: str,
    ) -> None:
        """Move groundtruth task back to start."""
