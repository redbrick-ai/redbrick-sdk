"""Abstract interface to exporting."""

from typing import Optional, List, Dict, Tuple
from abc import ABC, abstractmethod
import aiohttp


class LabelingControllerInterface(ABC):
    """Abstract interface to Labeling APIs."""

    @abstractmethod
    def get_labeling_tasks(
        self, org_id: str, project_id: str, stage_name: str, count: int = 5
    ) -> List[Dict]:
        """Get labeling tasks."""

    @abstractmethod
    async def put_labeling_results(
        self,
        session: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        stage_name: str,
        task_id: str,
        labels: List[Dict],
    ) -> None:
        """Put Labeling results."""

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
    def assign_task(
        self, org_id: str, project_id: str, stage_name: str, task_id: str, email: str
    ) -> None:
        """Assign task to specified email."""

    @abstractmethod
    def get_tasks_queue(
        self,
        org_id: str,
        project_id: str,
        stage_name: str,
        first: int,
        cursor: Optional[str] = None,
    ) -> Tuple[List[Dict], str]:
        """Get task queue."""

    @abstractmethod
    def get_task_queue_count(
        self, org_id: str, project_id: str, stage_name: str,
    ) -> int:
        """Get the length of the task queue for showing loading."""
