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
        Create a datapoint and returns its taskId.

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
        labels_data: Optional[str],
        labels_map: Optional[List[Dict]] = None,
        is_ground_truth: bool = False,
    ) -> Dict:
        """
        Create a datapoint and returns its taskId.

        Name must be unique in the project.
        """
        query_string = """
            mutation createDatapointSDK(
                $orgId: UUID!
                $projectId: UUID!
                $items: [String!]!
                $name: String!
                $storageId: UUID!
                $labelsData: String
                $labelsMap: [LabelMapInput!]
                $isGroundTruth: Boolean!
            ) {
                createDatapoint(
                    orgId: $orgId
                    projectId: $projectId
                    items: $items
                    name: $name
                    storageId: $storageId
                    labelsData: $labelsData
                    labelsMap: $labelsMap
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
            "labelsData": labels_data,
            "labelsMap": labels_map,
            "isGroundTruth": is_ground_truth,
        }
        response = await self.client.execute_query_async(
            aio_client, query_string, query_variables
        )
        return response.get("createDatapoint", {})

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
        query_string = """
            mutation itemListUploadSuccessSDK(
                $orgId: UUID!
                $projectId: UUID!
                $payload: ItemsListUploadSuccessInput!
            ) {
                itemListUploadSuccess(
                    orgId: $orgId
                    projectId: $projectId
                    payload: $payload
                ) {
                    ok
                }
            }
        """

        query_variables = {
            "orgId": org_id,
            "projectId": project_id,
            "payload": {
                "orgId": org_id,
                "projectId": project_id,
                "filePath": file_path,
                "fileName": file_name,
                "fileType": file_type,
                "uploadId": project_id,
                "dataType": data_type,
                "taskType": task_type,
                "storageId": storage_id,
                "isGroundTruth": is_ground_truth,
            },
        }
        response = await self.client.execute_query_async(
            aio_client, query_string, query_variables
        )
        return response.get("itemListUploadSuccess", {})

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
