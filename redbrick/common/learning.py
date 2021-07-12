"""Abstract interface to active learning API."""


from typing import Optional, List, Dict, Tuple
from abc import ABC, abstractmethod

import aiohttp


class LearningControllerInterface(ABC):
    """Abstract interface to Active Learning APIs."""

    @abstractmethod
    def check_for_job(
        self, org_id: str, project_id: str, stage_name: str
    ) -> Optional[int]:
        """Check for a job, returns cycle number."""

    @abstractmethod
    def get_batch_of_tasks(
        self,
        org_id: str,
        project_id: str,
        stage_name: str,
        first: int = 50,
        cursor: Optional[str] = None,
    ) -> Tuple[List[dict], Optional[str]]:
        """Get batch of tasks, paginated."""

    @abstractmethod
    def get_taxonomy_and_type(
        self, org_id: str, project_id: str, stage_name: str
    ) -> Tuple[dict, str]:
        """Get the taxonomy for active learning."""

    @abstractmethod
    def send_batch_learning_results(
        self,
        org_id: str,
        project_id: str,
        stage_name: str,
        cycle: int,
        tasks: List[Dict],
    ) -> None:
        """
        Send a batch of learning results.

        tasks is a list of dictionaries containing the following keys:
        {
            "taskId": "<>",
            "score": [0,1],
            "labels": { }  // see standard label format
        }
        """

    @abstractmethod
    async def send_batch_learning_results_async(
        self,
        aio_client: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        stage_name: str,
        cycle: int,
        tasks: List[Dict],
    ) -> None:
        """Perform send_batch_learning_results with asyncio."""

    @abstractmethod
    def set_cycle_status(
        self,
        org_id: str,
        project_id: str,
        stage_name: str,
        cycle: int,
        cycle_status: str,
    ) -> None:
        """Set status of current training cycle."""
