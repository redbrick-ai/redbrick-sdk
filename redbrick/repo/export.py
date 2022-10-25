"""Repo for accessing export apis."""
from typing import Optional, List, Dict, Sequence, Tuple
from datetime import datetime
from dateutil import parser  # type: ignore

import aiohttp

from redbrick.common.export import ExportControllerInterface
from redbrick.common.client import RBClient
from redbrick.repo.shards import DATAPOINT_SHARD, TASK_DATA_SHARD, TASK_SHARD


class ExportRepo(ExportControllerInterface):
    """Handle API requests to get export data."""

    def __init__(self, client: RBClient) -> None:
        """Construct ExportRepo."""
        self.client = client

    def datapoints_in_project(
        self, org_id: str, project_id: str, stage_name: Optional[str] = None
    ) -> int:
        """Get number of datapoints in project."""
        query_string = """
        query tasksPagedSDK($orgId: UUID!, $projectId: UUID!, $stageName: String, $first: Int) {
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
        till_time: Optional[datetime] = None,
        presign_items: bool = False,
        with_consensus: bool = False,
        first: int = 50,
        cursor: Optional[str] = None,
    ) -> Tuple[List[Dict], Optional[str], Optional[datetime]]:
        """Get the latest datapoints."""
        # pylint: disable=too-many-locals
        query_string = f"""
        query tasksPagedSDK(
            $orgId: UUID!
            $projectId: UUID!
            $stageName: String
            $cacheTime: DateTime
            $tillTime: DateTime
            $first: Int
            $cursor: String
        ) {{
            tasksPaged(
                orgId: $orgId
                projectId: $projectId
                stageName: $stageName
                cacheTime: $cacheTime
                tillTime: $tillTime
                first: $first
                after: $cursor
            ) {{
                entries {{
                    taskId
                    dpId
                    currentStageName
                    currentStageSubTask{"(consensus: true)" if with_consensus else ""} {{
                        {TASK_SHARD}
                    }}
                    latestTaskData {{
                        {DATAPOINT_SHARD.format(
                            "itemsPresigned:items(presigned: true)" if presign_items else ""
                        )}
                        {TASK_DATA_SHARD}
                    }}
                }}
                cursor
                cacheTime
            }}
        }}
        """
        # EXECUTE THE QUERY
        query_variables = {
            "orgId": org_id,
            "projectId": project_id,
            "stageName": stage_name,
            "cacheTime": None if cache_time is None else cache_time.isoformat(),
            "tillTime": None if till_time is None else till_time.isoformat(),
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
        manual_labeling_filters: Optional[Dict] = None,
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
            $manualLabelingFilters: TasksFilter
            $first: Int
            $after: String
        ) {
            genericTasks(
                orgId: $orgId
                projectId: $projectId
                stageName: $stageName
                taskSearch: $taskSearch
                manualLabelingFilters: $manualLabelingFilters
                first: $first
                after: $after
            ) {
                entries {
                    taskId
                    datapoint {
                        name
                        items
                        itemsPresigned: items(presigned: true)
                    }
                    currentStageName
                    createdAt
                    currentStageSubTask {
                        ... on LabelingTask {
                            state
                            assignedTo {
                                userId
                                email
                            }
                        }
                    }
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
            "manualLabelingFilters": manual_labeling_filters,
            "first": first,
            "after": after,
        }

        result = self.client.execute_query(query_string, query_variables, False)
        generic_tasks = result.get("genericTasks", {}) or {}
        entries: List[Dict] = generic_tasks.get("entries", []) or []  # type: ignore

        return entries, generic_tasks.get("cursor")

    def presign_items(
        self, org_id: str, storage_id: str, items: Sequence[Optional[str]]
    ) -> List[Optional[str]]:
        """Presign download items."""
        query = """
        query presignItems(
            $orgId: UUID!
            $storageId: UUID!
            $items: [String]!
        ) {
            presignItems(orgId: $orgId, storageId: $storageId, items: $items)
        }
        """

        variables = {"orgId": org_id, "storageId": storage_id, "items": items}

        response = self.client.execute_query(query, variables)
        presigned_items: List[Optional[str]] = response.get("presignItems", [])
        return presigned_items
