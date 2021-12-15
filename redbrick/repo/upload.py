"""Abstract interface to upload."""

from typing import List, Dict, Optional, Any
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
        is_ground_truth: bool = False,
    ) -> Dict:
        """
        Create a datapoint and returns its dpId.

        Name must be unique in the project.
        """
        query_string = """
            mutation(
                $orgId: UUID!
                $projectId: UUID!
                $items: [String!]!
                $name: String!
                $storageId: UUID!
                $labels: [LabelInput!]
                $isGroundTruth: Boolean!
            ) {
                createDatapoint(
                    orgId: $orgId
                    projectId: $projectId
                    items: $items
                    name: $name
                    storageId: $storageId
                    labels: $labels
                    isGroundTruth: $isGroundTruth
                ) {
                    taskId
                }
            }
        """

        query_variables = {
            "orgId": org_id,
            "projectId": project_id,
            "items": items,
            "name": name,
            "storageId": storage_id,
            "labels": labels or [],
            "isGroundTruth": is_ground_truth,
        }

        response = await self.client.execute_query_async(
            aio_client, query_string, query_variables
        )
        assert isinstance(response["createDatapoint"], dict)
        return response["createDatapoint"]

    def items_upload_presign(
        self, org_id: str, project_id: str, files: List[str], file_type: List[str]
    ) -> List[Dict[Any, Any]]:
        """Return presigned URLs to upload files."""
        query_string = """
            query itemsUploadPresign(
                $orgId:UUID!,
                $projectId: UUID!,
                $files: [String]!,
                $fileType:[String]!
            ){
                itemsUploadPresign(
                    orgId:$orgId,
                    projectId: $projectId,
                    files:$files,
                    fileType:$fileType
                ) {
                    items {
                        presignedUrl,
                        filePath,
                        fileName
                    }
                }
            }
        """

        query_variables = {
            "orgId": org_id,
            "projectId": project_id,
            "files": files,
            "fileType": file_type,
        }
        result = self.client.execute_query(query_string, query_variables)
        assert isinstance(result["itemsUploadPresign"]["items"], list)
        return result["itemsUploadPresign"]["items"]

    def upload_image(self, org_id: str, project_id: str, file_path: Path) -> str:
        """Upload a local image and add labels."""
        raise NotImplementedError()

    async def upload_image_async(
        self, org_id: str, project_id: str, file_path: Path
    ) -> str:
        """Upload a local image and add labels."""
        raise NotImplementedError()
