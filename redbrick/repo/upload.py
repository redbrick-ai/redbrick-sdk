"""Abstract interface to upload."""

from typing import List, Dict, Optional
from pathlib import Path

import aiohttp

from redbrick.common.client import RBClient
from redbrick.common.upload import UploadControllerInterface


class UploadRepo(UploadControllerInterface):
    """Handle communication with backend relating to uploads."""

    def __init__(self, client: RBClient) -> None:
        """Construct ExportRepo."""
        self.client = client

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
        raise NotImplementedError()

    async def create_datapoint_async(
        self,
        aio_client: aiohttp.ClientSession,
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
        query_string = """
            mutation(
                $orgId: UUID!
                $items: [String!]!
                $name: String!
                $dsetName: String!
                $storageId: UUID!
                $lsetName: String!
                $labels: [LabelInput!]
            ) {
                createDatapoint(
                    orgId: $orgId
                    items: $items
                    name: $name
                    dsetName: $dsetName
                    storageId: $storageId
                    lsetName: $lsetName
                    labels: $labels
                ) {
                    dpId
                }
            }
        """

        query_variables = {
            "orgId": org_id,
            "items": items,
            "name": name,
            "dsetName": project_id,
            "storageId": storage_id,
            "lsetName": project_id + "-input",
            "labels": labels or [],
        }

        await self.client.execute_query_async(aio_client, query_string, query_variables)

    def upload_image(self, org_id: str, project_id: str, file_path: Path) -> str:
        """Upload a local image and add labels."""
        raise NotImplementedError()

    async def upload_image_async(
        self, org_id: str, project_id: str, file_path: Path
    ) -> str:
        """Upload a local image and add labels."""
        raise NotImplementedError()
