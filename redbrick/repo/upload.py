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
                $isGroundTruth: Boolean!
            ) {
                createDatapoint(
                    orgId: $orgId
                    items: $items
                    name: $name
                    dsetName: $dsetName
                    storageId: $storageId
                    lsetName: $lsetName
                    labels: $labels
                    isGroundTruth: $isGroundTruth
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
            "isGroundTruth": is_ground_truth,
        }

        await self.client.execute_query_async(aio_client, query_string, query_variables)

    def items_upload_presign(
        self, org_id: str, files: List[str], dataset: str, file_type: List[str]
    ) -> List[Dict[Any, Any]]:
        """Return presigned URLs to upload files."""
        query_string = """
            query itemsUploadPresign($orgId:UUID!, $files: [String]!,
            $dataset:String!, $fileType:[String]!){
                itemsUploadPresign(orgId:$orgId, files:$files, dataset:$dataset,
                fileType:$fileType) {
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
            "files": files,
            "dataset": dataset,
            "fileType": file_type,
        }
        result = self.client.execute_query(query_string, query_variables)
        return result["itemsUploadPresign"]["items"]

    def upload_image(self, org_id: str, project_id: str, file_path: Path) -> str:
        """Upload a local image and add labels."""
        raise NotImplementedError()

    async def upload_image_async(
        self, org_id: str, project_id: str, file_path: Path
    ) -> str:
        """Upload a local image and add labels."""
        raise NotImplementedError()
