"""Abstract interface to upload."""

from typing import List, Dict, Optional, Any, Sequence
from abc import ABC, abstractmethod

import aiohttp


class UploadControllerInterface(ABC):
    """Abstract interface to define methods for Upload."""

    @abstractmethod
    async def create_datapoint_async(  # pylint: disable=too-many-locals
        self,
        aio_client: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        storage_id: str,
        name: str,
        items: List[str],
        heat_maps: Optional[List[Dict]],
        transforms: Optional[List[Dict]],
        labels_data: Optional[str],
        labels_map: Optional[List[Dict]] = None,
        series_info: Optional[List[Dict]] = None,
        meta_data: Optional[str] = None,
        is_ground_truth: bool = False,
        pre_assign: Optional[Dict] = None,
        priority: Optional[float] = None,
    ) -> Dict:
        """
        Create a datapoint and returns its taskId.

        Name must be unique in the project.
        """

    @abstractmethod
    async def update_items_async(
        self,
        aio_client: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        storage_id: str,
        task_id: str,
        items: Optional[List[str]] = None,
        series_info: Optional[List[Dict]] = None,
        heat_maps: Optional[List[Dict]] = None,
        transforms: Optional[List[Dict]] = None,
        meta_data: Optional[str] = None,
    ) -> Dict:
        """Update items in a datapoint."""

    @abstractmethod
    def items_upload_presign(
        self, org_id: str, project_id: str, files: List[str], file_type: List[str]
    ) -> List[Dict[Any, Any]]:
        """Get a presigned url for uploading items."""

    @abstractmethod
    async def delete_tasks(
        self,
        aio_client: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        task_ids: List[str],
    ) -> bool:
        """Delete tasks in a project."""

    @abstractmethod
    async def delete_tasks_by_name(
        self,
        aio_client: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        task_names: List[str],
    ) -> bool:
        """Delete tasks in a project by task names."""

    @abstractmethod
    async def generate_items_list(
        self,
        aio_client: aiohttp.ClientSession,
        files: List[str],
        import_type: str,
        as_study: bool = False,
        windows: bool = False,
    ) -> str:
        """Generate direct upload items list."""

    @abstractmethod
    async def validate_and_convert_to_import_format(
        self,
        aio_client: aiohttp.ClientSession,
        original: str,
        convert: Optional[bool] = None,
        storage_id: Optional[str] = None,
    ) -> Dict:
        """Validate and convert tasks format."""

    @abstractmethod
    def import_tasks_from_workspace(
        self,
        org_id: str,
        project_id: str,
        source_project_id: str,
        task_search: List[Dict],
        with_labels: bool = False,
    ) -> Dict:
        """Import tasks from another project in the same workspace."""

    @abstractmethod
    async def update_priority(
        self,
        session: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        tasks: List[Dict],
    ) -> Optional[str]:
        """Update tasks priorities."""

    @abstractmethod
    async def update_labels(
        self,
        session: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        task_id: str,
        labels: str,
        labels_map: Optional[Sequence[Optional[Dict]]] = None,
        finalize: bool = False,
        time_spent_ms: Optional[int] = None,
        extra_data: Optional[Dict] = None,
    ) -> None:
        """Update tasks labels."""
