"""Abstract interface to upload."""

from typing import List, Dict, Optional, Any
from abc import ABC, abstractmethod

from pathlib import Path

import aiohttp


class UploadControllerInterface(ABC):
    """Abstract interface to define methods for Upload."""

    @abstractmethod
    def create_datapoint(
        self,
        org_id: str,
        project_id: str,
        storage_id: str,
        name: str,
        items: List[str],
        labels: Optional[List[Dict]],
    ) -> str:
        """
        Create a datapoint and returns its taskId.

        Name must be unique in the project.
        """

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
        is_ground_truth: bool = False,
    ) -> Dict:
        """
        Create a datapoint and returns its taskId.

        Name must be unique in the project.
        """

    @abstractmethod
    async def item_upload_async(
        self,
        aio_client: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        storage_id: str,
        data_type: str,
        task_type: str,
        file_path: str,
        file_name: str,
        file_type: str,
        is_ground_truth: bool = False,
    ) -> Dict:
        """Upload an item."""

    @abstractmethod
    def upload_image(
        self,
        org_id: str,
        project_id: str,
        file_path: Path,
    ) -> str:
        """Upload a local image and add labels."""

    @abstractmethod
    async def upload_image_async(
        self,
        org_id: str,
        project_id: str,
        file_path: Path,
    ) -> str:
        """Upload a local image and add labels."""

    @abstractmethod
    def items_upload_presign(
        self, org_id: str, project_id: str, files: List[str], file_type: List[str]
    ) -> List[Dict[Any, Any]]:
        """Get a presigned url for uploading items."""
