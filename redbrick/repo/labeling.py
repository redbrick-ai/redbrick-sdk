"""Abstract interface to exporting."""

from typing import Optional, List, Dict

from redbrick.common.client import RBClient
from redbrick.common.labeling import LabelingControllerInterface


class LabelingRepo(LabelingControllerInterface):
    def __init__(self, client: RBClient) -> None:
        """Construct ExportRepo."""
        self.client = client

    def get_labeling_tasks(
        self, org_id: str, project_id: str, stage_name: str, count: int = 5
    ) -> List[Dict]:
        """Get labeling tasks."""

    def put_labeling_results(
        self,
        org_id: str,
        project_id: str,
        stage_name: str,
        task_id: str,
        labels: List[Dict],
    ) -> None:
        """Put Labeling results."""

    def put_review_task_result(
        self,
        org_id: str,
        project_id: str,
        stage_name: str,
        task_id: str,
        review_val: bool,
    ) -> None:
        """Put review result for task."""
