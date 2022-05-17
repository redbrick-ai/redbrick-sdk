"""Repo for accessing export apis."""
from typing import Optional, List, Dict, Tuple
from datetime import datetime
from dateutil import parser

import aiohttp

from redbrick.common.export import ExportControllerInterface
from redbrick.common.client import RBClient
from redbrick.repo.shards import TAXONOMY_SHARD, LATEST_TASKDATA_SHARD


class ExportRepo(ExportControllerInterface):
    """Handle API requests to get export data."""

    def __init__(self, client: RBClient) -> None:
        """Construct ExportRepo."""
        self.client = client

    def get_datapoints_input(
        self,
        org_id: str,
        project_id: str,
        first: int = 50,
        presign: bool = False,
        cursor: Optional[str] = None,
    ) -> Tuple[List[Dict], Optional[str]]:
        """Get datapoints that were uploaded to the project."""
        raise NotImplementedError()

    def get_output_info(self, org_id: str, project_id: str) -> Dict:
        """Get info about the output labelset and taxonomy."""
        query_string = (
            """
        query ($orgId: UUID!, $name: String!){
            customGroup(orgId: $orgId, name:$name){
                dataType
                taskType
                datapointCount
                taxonomy {
                    %s
                    colorMap {
                        name
                        color
                        classid
                        trail
                        taskcategory
                    }
                }
            }
        }
        """
            % TAXONOMY_SHARD
        )

        # EXECUTE THE QUERY
        query_variables = {
            "orgId": org_id,
            "name": project_id + "-output",
        }

        result = self.client.execute_query(query_string, query_variables)

        temp: Dict = result["customGroup"]
        return temp

    def get_datapoints_output(
        self,
        org_id: str,
        project_id: str,
        first: int = 50,
        cursor: Optional[str] = None,
    ) -> Tuple[List[Dict], Optional[str]]:
        """Get datapoints that have made it to the output of the project."""
        query_string = """
        query ($orgId: UUID!, $projectId: UUID!, $name: String!,$first: Int, $cursor: String){
        customGroup(orgId: $orgId, name:$name){
            datapointsPaged(first:$first, after:$cursor) {
            entries {
                name
                itemsPresigned:items (presigned:true)
                items(presigned:false)
                task(projectId: $projectId) {
                    taskId
                }
                labelData(customGroupName: $name){
                    createdByEmail
                    labelsData(interpolate: true)
                    labelsMap {
                        labelName
                        imageIndex
                        imageName
                        seriesId
                    }
                }
            }
            cursor
            }
        }
        }
        """
        # EXECUTE THE QUERY
        query_variables = {
            "orgId": org_id,
            "name": project_id + "-output",
            "projectId": project_id,
            "cursor": cursor,
            "first": first,
        }

        result = self.client.execute_query(query_string, query_variables, False)
        custom_group = result.get("customGroup", {}) or {}
        datapoints_paged = custom_group.get("datapointsPaged", {}) or {}
        entries: List[Dict] = datapoints_paged.get("entries", []) or []  # type: ignore
        return entries, datapoints_paged.get("cursor")

    def datapoints_in_project(
        self, org_id: str, project_id: str, stage_name: Optional[str] = None
    ) -> int:
        """Get number of datapoints in project."""
        query_string = """
        query($orgId: UUID!, $projectId: UUID!, $stageName: String, $first: Int) {
            tasksPaged(
                orgId: $orgId
                projectId: $projectId
                stageName: $stageName
                first: $first
            ) {
                count
            }
        }
        """
        # EXECUTE THE QUERY
        query_variables = {
            "orgId": org_id,
            "projectId": project_id,
            "stageName": stage_name,
            "first": 0,
        }

        result = self.client.execute_query(query_string, query_variables)

        return int(result["tasksPaged"]["count"])

    def get_datapoints_latest(
        self,
        org_id: str,
        project_id: str,
        stage_name: Optional[str] = None,
        cache_time: Optional[datetime] = None,
        first: int = 50,
        cursor: Optional[str] = None,
    ) -> Tuple[List[Dict], Optional[str], Optional[datetime]]:
        """Get the latest datapoints."""
        query_string = (
            """
        query(
            $orgId: UUID!,
            $projectId: UUID!,
            $stageName: String,
            $cacheTime: DateTime,
            $first: Int,
            $cursor: String
        ) {
            tasksPaged(
                orgId: $orgId
                projectId: $projectId
                stageName: $stageName
                cacheTime: $cacheTime
                first: $first
                after: $cursor
            ) {
                entries {
                    taskId
                    dpId
                    currentStageName
                    %s
                }
                cursor
                cacheTime
            }
            }
        """
            % LATEST_TASKDATA_SHARD
        )
        # EXECUTE THE QUERY
        query_variables = {
            "orgId": org_id,
            "projectId": project_id,
            "stageName": stage_name,
            "cacheTime": None if cache_time is None else cache_time.isoformat(),
            "first": first,
            "cursor": cursor,
        }

        result = self.client.execute_query(query_string, query_variables, False)
        tasks_paged = result.get("tasksPaged", {}) or {}
        entries: List[Dict] = tasks_paged.get("entries", []) or []  # type: ignore
        new_cache_time: Optional[str] = tasks_paged.get("cacheTime")
        return (
            entries,
            tasks_paged.get("cursor"),
            parser.parse(new_cache_time) if new_cache_time else None,
        )

    def get_datapoint_latest(self, org_id: str, project_id: str, task_id: str) -> Dict:
        """Get the latest labels for a single bdatapoint."""
        query_string = (
            """
        query($orgId: UUID!, $projectId: UUID!, $taskId: UUID!) {
            task(
                orgId: $orgId
                projectId: $projectId
                taskId: $taskId
            ) {
                taskId
                currentStageName
                %s
            }
            }
        """
            % LATEST_TASKDATA_SHARD
        )
        # EXECUTE THE QUERY
        query_variables = {
            "orgId": org_id,
            "projectId": project_id,
            "taskId": task_id,
        }

        result: Dict[str, Dict] = self.client.execute_query(
            query_string, query_variables, False
        )

        return result.get("task", {}) or {}

    async def get_labels(
        self, session: aiohttp.ClientSession, org_id: str, project_id: str, dp_id: str
    ) -> Dict:
        """Get input labels."""
        query = """
        query dataPoint(
            $orgId: UUID!
            $dpId: UUID!
            $name: String!
        ) {
            dataPoint(orgId: $orgId, dpId: $dpId) {
                labelData(customGroupName: $name) {
                    dpId
                    labelsData
                }
            }
        }
        """

        variables = {
            "orgId": org_id,
            "dpId": dp_id,
            "name": f"{project_id}-input",
        }

        response = await self.client.execute_query_async(session, query, variables)
        label_data: Dict = response.get("dataPoint", {}).get("labelData", {})
        return label_data

    def task_search(
        self,
        org_id: str,
        project_id: str,
        stage_name: Optional[str] = None,
        task_search: Optional[str] = None,
        first: int = 50,
        after: Optional[str] = None,
    ) -> Tuple[List[Dict], Optional[str]]:
        """Task search."""
        query_string = """
        query tasksList(
            $orgId: UUID!
            $projectId: UUID!
            $stageName: String
            $taskSearch: String
            $first: Int
            $after: String
        ) {
            genericTasks(
                orgId: $orgId
                projectId: $projectId
                stageName: $stageName
                taskSearch: $taskSearch
                first: $first
                after: $after
            ) {
                entries {
                    taskId
                    datapoint {
                        name
                    }
                    currentStageName
                    createdAt
                }
                cursor
            }
        }
        """

        query_variables = {
            "orgId": org_id,
            "projectId": project_id,
            "stageName": stage_name,
            "taskSearch": task_search,
            "first": first,
            "after": after,
        }

        result = self.client.execute_query(query_string, query_variables, False)
        generic_tasks = result.get("genericTasks", {}) or {}
        entries: List[Dict] = generic_tasks.get("entries", []) or []  # type: ignore

        return entries, generic_tasks.get("cursor")

    def presign_items(
        self, org_id: str, storage_id: str, items: List[str]
    ) -> List[str]:
        """Presign download items."""
        query = """
        query presignItems(
            $orgId: UUID!
            $storageId: UUID!
            $items: [String!]!
        ) {
            presignItems(orgId: $orgId, storageId: $storageId, items: $items)
        }
        """

        variables = {"orgId": org_id, "dpId": storage_id, "items": items}

        response = self.client.execute_query(query, variables)
        presigned_items: List[str] = response.get("presignItems", [])
        return presigned_items
