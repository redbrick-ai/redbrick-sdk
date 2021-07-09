"""Abstract interface to upload."""

from typing import List, Dict, Optional
from abc import ABC, abstractmethod

from pathlib import Path

import aiohttp


class UploadControllerInterface(ABC):
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
        Create a datapoint and returns its dpId.

        Name must be unique in the project.
        """

    @abstractmethod
    async def create_datapoint_async(
        self,
        aio_http_session: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        storage_id: str,
        name: str,
        items: List[str],
        labels: Optional[List[Dict]],
    ) -> None:
        """
        Create a datapoint and returns its dpId.

        Name must be unique in the project.
        """

    @abstractmethod
    def upload_image(self, org_id: str, project_id: str, file_path: Path,) -> str:
        """Upload a local image and add labels."""

    @abstractmethod
    async def upload_image_async(
        self, org_id: str, project_id: str, file_path: Path,
    ) -> str:
        """Upload a local image and add labels."""
