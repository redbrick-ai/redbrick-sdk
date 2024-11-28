"""Abstract interface to upload."""

import json
from typing import List, Dict, Optional, Any, Sequence

import aiohttp

from redbrick.common.client import RBClient
from redbrick.common.upload import UploadControllerInterface


class UploadRepo(UploadControllerInterface):
    """Handle communication with backend relating to uploads."""

    def __init__(self, client: RBClient) -> None:
        """Construct ExportRepo."""
        self.client = client

    async def create_datapoint_async(
        self,
        aio_client: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        storage_id: str,
        name: str,
        items: List[str],
        heat_maps: Optional[List[Dict]],
        transforms: Optional[List[Dict]],
        centerlines: Optional[List[Dict]],
        labels_data: Optional[str],
        labels_map: Optional[List[Dict]] = None,
        series_info: Optional[List[Dict]] = None,
        meta_data: Optional[Dict] = None,
        is_ground_truth: bool = False,
        pre_assign: Optional[Dict] = None,
        priority: Optional[float] = None,
        attributes: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        Create a datapoint and returns its taskId.

        Name must be unique in the project.
        """
        # pylint: disable=too-many-locals
        query_string = """
            mutation createDatapointSDK(
                $orgId: UUID!
                $projectId: UUID!
                $items: [String!]!
                $heatMaps: [HeatMapInput!]
                $transforms: [TransformInput!]
                $centerline: [CenterlineInput!]
                $name: String!
                $storageId: UUID!
                $labelsData: String
                $labelsMap: [LabelMapInput]
                $seriesInfo: [SeriesInfoInput!]
                $metaData: String
                $isGroundTruth: Boolean!
                $preAssign: String
                $priority: Float
                $attributes: JSONString
            ) {
                createDatapoint(
                    orgId: $orgId
                    projectId: $projectId
                    items: $items
                    heatMaps: $heatMaps
                    transforms: $transforms
                    centerline: $centerline
                    name: $name
                    storageId: $storageId
                    labelsData: $labelsData
                    labelsMap: $labelsMap
                    seriesInfo: $seriesInfo
                    metaData: $metaData
                    isGroundTruth: $isGroundTruth
                    preAssign: $preAssign
                    priority: $priority
                    attributes: $attributes
                ) {
                    taskId
                    taskIds
                }
            }
        """

        query_variables = {
            "orgId": org_id,
            "projectId": project_id,
            "items": items,
            "heatMaps": heat_maps,
            "transforms": transforms,
            "centerline": (
                [
                    {**centerline, "centerline": json.dumps(centerline["centerline"])}
                    for centerline in centerlines
                ]
                if centerlines
                else None
            ),
            "name": name,
            "storageId": storage_id,
            "labelsData": labels_data,
            "labelsMap": labels_map,
            "seriesInfo": series_info,
            "metaData": (
                json.dumps(meta_data, separators=(",", ":")) if meta_data else None
            ),
            "isGroundTruth": is_ground_truth,
            "preAssign": json.dumps(pre_assign, separators=(",", ":")),
            "priority": priority,
            "attributes": (
                json.dumps(attributes, separators=(",", ":")) if attributes else None
            ),
        }
        response = await self.client.execute_query_async(
            aio_client, query_string, query_variables
        )
        return response.get("createDatapoint", {})

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
        centerlines: Optional[List[Dict]] = None,
        meta_data: Optional[Dict] = None,
    ) -> Dict:
        """Update items in a datapoint."""
        query_string = """
            mutation updateTaskItemsSDK(
                $orgId: UUID!
                $projectId: UUID!
                $storageId: UUID!
                $taskId: UUID!
                $items: [String!]
                $seriesInfo: [SeriesInfoInput!]
                $heatMaps: [HeatMapInput!]
                $transforms: [TransformInput!]
                $centerline: [CenterlineInput!]
                $metaData: String
            ) {
                updateTaskItems(
                    orgId: $orgId
                    projectId: $projectId
                    storageId: $storageId
                    taskId: $taskId
                    items: $items
                    seriesInfo: $seriesInfo
                    heatMaps: $heatMaps
                    transforms: $transforms
                    centerline: $centerline
                    metaData: $metaData
                ) {
                    ok
                    message
                }
            }
        """

        query_variables = {
            "orgId": org_id,
            "projectId": project_id,
            "storageId": storage_id,
            "taskId": task_id,
            "items": items,
            "seriesInfo": series_info,
            "heatMaps": heat_maps,
            "transforms": transforms,
            "centerline": (
                [
                    {**centerline, "centerline": json.dumps(centerline["centerline"])}
                    for centerline in centerlines
                ]
                if centerlines
                else None
            ),
            "metaData": (
                json.dumps(meta_data, separators=(",", ":")) if meta_data else None
            ),
        }
        response = await self.client.execute_query_async(
            aio_client, query_string, query_variables
        )
        return response.get("updateTaskItems", {})

    def items_upload_presign(
        self, org_id: str, project_id: str, files: List[str], file_type: List[str]
    ) -> List[Dict[Any, Any]]:
        """Return presigned URLs to upload files."""
        query_string = """
            query itemsUploadPresignSDK(
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
        presigned: List[Dict] = result["itemsUploadPresign"]["items"]
        return presigned

    async def delete_tasks(
        self,
        aio_client: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        task_ids: List[str],
    ) -> bool:
        """Delete tasks in a project."""
        query_string = """
        mutation deleteTasksSDK($orgId: UUID!, $projectId: UUID!, $taskIds: [UUID!]) {
            deleteTasks(
                orgId: $orgId
                projectId: $projectId
                taskIds: $taskIds
            ) {
                ok
            }
        }
        """
        # EXECUTE THE QUERY
        query_variables = {
            "orgId": org_id,
            "projectId": project_id,
            "taskIds": task_ids,
        }

        result: Dict[str, Dict] = await self.client.execute_query_async(
            aio_client, query_string, query_variables
        )

        return (result.get("deleteTasks", {}) or {}).get("ok", False)

    async def delete_tasks_by_name(
        self,
        aio_client: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        task_names: List[str],
    ) -> bool:
        """Delete tasks in a project by task names."""
        query_string = """
        mutation deleteTasksNamesSDK($orgId: UUID!, $projectId: UUID!, $taskNames: [String!]) {
            deleteTasks(
                orgId: $orgId
                projectId: $projectId
                taskNames: $taskNames
            ) {
                ok
            }
        }
        """
        # EXECUTE THE QUERY
        query_variables = {
            "orgId": org_id,
            "projectId": project_id,
            "taskNames": task_names,
        }

        result: Dict[str, Dict] = await self.client.execute_query_async(
            aio_client, query_string, query_variables
        )

        return (result.get("deleteTasks", {}) or {}).get("ok", False)

    async def generate_items_list(
        self,
        aio_client: aiohttp.ClientSession,
        files: List[str],
        import_type: str,
        as_study: bool = False,
        windows: bool = False,
    ) -> str:
        """Generate direct upload items list."""
        query_string = """
            query generateItemsListSDK(
                $importType: ImportType!
                $files: [String]!
                $groupedByStudy: Boolean!
                $windows: Boolean
            ) {
                generateItemsList(
                    importType: $importType
                    files: $files
                    groupedByStudy: $groupedByStudy
                    windows: $windows
                )
            }
        """

        query_variables = {
            "importType": import_type,
            "files": files,
            "groupedByStudy": as_study,
            "windows": windows,
        }
        result = await self.client.execute_query_async(
            aio_client, query_string, query_variables
        )
        items_list: str = result["generateItemsList"]
        return items_list

    async def validate_and_convert_to_import_format(
        self,
        aio_client: aiohttp.ClientSession,
        original: str,
        convert: Optional[bool] = None,
        storage_id: Optional[str] = None,
    ) -> Dict:
        """Validate and convert tasks format."""
        query_string = """
        query validateAndConvertToImportFormatSDK(
            $original: String!
            $convert: Boolean
            $storageId: UUID
        ) {
            validateAndConvertToImportFormat(
                original: $original
                convert: $convert
                storageId: $storageId
            ) {
                isValid
                error
                converted
            }
        }
        """
        query_variables = {
            "original": original,
            "convert": convert,
            "storageId": storage_id,
        }

        result: Dict[str, Dict] = await self.client.execute_query_async(
            aio_client, query_string, query_variables
        )

        return result.get("validateAndConvertToImportFormat", {}) or {}

    def import_tasks_from_workspace(
        self,
        org_id: str,
        project_id: str,
        source_project_id: str,
        task_search: List[Dict],
        with_labels: bool = False,
    ) -> Dict:
        """Import tasks from another project in the same workspace."""
        query_string = """
            mutation importTasksFromWorkspaceSDK(
                $orgId: UUID!
                $projectId: UUID!
                $sourceProjectId: UUID!
                $tasks: [TaskMetaDataInput!]!
                $withLabels: Boolean
            ) {
                importTasksFromWorkspace(
                    orgId: $orgId
                    projectId: $projectId
                    sourceProjectId: $sourceProjectId
                    tasks: $tasks
                    withLabels: $withLabels
                ) {
                    ok
                    message
                }
            }
        """

        query_variables = {
            "orgId": org_id,
            "projectId": project_id,
            "sourceProjectId": source_project_id,
            "tasks": task_search,
            "withLabels": with_labels,
        }
        result = self.client.execute_query(query_string, query_variables)
        return result.get("importTasksFromProject", {}) or {}

    async def update_priority(
        self,
        session: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        tasks: List[Dict],
    ) -> Optional[str]:
        """Update tasks priorities."""
        query_string = """
        mutation updateTasksPrioritiesSDK(
            $orgId: UUID!
            $projectId: UUID!
            $tasks: [UpdateTaskPriorityInput!]!
        ) {
            updateTasksPriorities(
                orgId: $orgId
                projectId: $projectId
                tasks: $tasks
            ) {
                ok
                message
            }
        }
        """

        # EXECUTE THE QUERY
        query_variables = {
            "orgId": org_id,
            "projectId": project_id,
            "tasks": tasks,
        }

        response = await self.client.execute_query_async(
            session, query_string, query_variables
        )
        return (response.get("updateTasksPriorities", {}) or {}).get("message")

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
        query_string = """
        mutation updateTasksLabelsSDK(
            $orgId: UUID!
            $projectId: UUID!
            $taskId: UUID!
            $labelsData: String
            $labelsMap: [LabelMapInput]
            $finalize: Boolean
            $timeSpentMs: Int
            $extraData: JSONString
        ) {
            putLabels(
                orgId: $orgId
                projectId: $projectId
                taskId: $taskId
                labelsData: $labelsData
                labelsMap: $labelsMap
                finalize: $finalize
                timeSpentMs: $timeSpentMs
                extraData: $extraData
            ) {
                ok
                message
            }
        }
        """

        # EXECUTE THE QUERY
        query_variables = {
            "orgId": org_id,
            "projectId": project_id,
            "taskId": task_id,
            "labelsData": labels,
            "labelsMap": labels_map,
            "finalize": finalize,
            "timeSpentMs": time_spent_ms,
            "extraData": json.dumps(extra_data),
        }

        await self.client.execute_query_async(session, query_string, query_variables)
