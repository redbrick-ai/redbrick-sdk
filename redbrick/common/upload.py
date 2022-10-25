"""Abstract interface to upload."""

from typing import List, Dict, Optional, Any
from abc import ABC, abstractmethod

import aiohttp


class UploadControllerInterface(ABC):
    """Abstract interface to define methods for Upload."""

    @abstractmethod
    async def create_datapoint_async(
        self,
        aio_client: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        storage_id: str,
        name: str,
        items: List[str],
        labels_data: Optional[str],
        labels_map: Optional[List[Dict]] = None,
        series_info: Optional[List[Dict]] = None,
        meta_data: Optional[str] = None,
        is_ground_truth: bool = False,
        pre_assign: Optional[Dict] = None,
    ) -> Dict:
        """
        Create a datapoint and returns its taskId.

        Name must be unique in the project.
        """

    @abstractmethod
    def items_upload_presign(
        self, org_id: str, project_id: str, files: List[str], file_type: List[str]
    ) -> List[Dict[Any, Any]]:
        """Get a presigned url for uploading items."""

    @abstractmethod
    def delete_tasks(self, org_id: str, project_id: str, task_ids: List[str]) -> bool:
        """Delete tasks in a project."""

    @abstractmethod
    def generate_items_list(
        self,
        files: List[str],
        import_type: str,
        as_study: bool = False,
        windows: bool = False,
    ) -> str:
        """Generate direct upload items list."""

    @abstractmethod
    def validate_and_convert_to_import_format(
        self,
        original: str,
        convert: Optional[bool] = None,
        storage_id: Optional[str] = None,
    ) -> Dict:
        """Validate and convert tasks format."""
