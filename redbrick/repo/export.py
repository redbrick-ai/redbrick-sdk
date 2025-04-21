"""Repo for accessing export apis."""

from typing import Any, Optional, List, Dict, Sequence, Tuple
from datetime import datetime
from dateutil import parser  # type: ignore

from redbrick.common.export import ExportRepo, TaskFilterParams
from redbrick.common.client import RBClient
from redbrick.repo.shards import datapoint_shard, task_shard, router_task_shard


class ExportRepoImpl(ExportRepo):
    """Handle API requests to get export data."""

    def __init__(self, client: RBClient) -> None:
        """Construct ExportRepoImpl."""
        self.client = client

    def get_dataset_imports(
        self, org_id: str, data_store: str
    ) -> Tuple[List[Dict], str]:
        """Get data store import."""
        query_string = """
            query dataStoreImports($orgId: UUID!, $dataStore: String!, $first: Int, $after: String, $createdBy: CustomUUID, $createdAfter: DateTime, $createdBefore: DateTime){
                dataStoreImports(orgId: $orgId, dataStore: $dataStore, first: $first, after: $after, createdBy: $createdBy, createdAfter: $createdAfter, createdBefore: $createdBefore){
                    entries{
                        orgId
                        datastore
                        name
                        importId
                        createdAt
                        createdBy
                        status
                        updatedAt
                        taskCount
                        failureLogs
                    }
                    cursor
                }
            }
        """
        query_variables = {
            "orgId": org_id,
            "dataStore": data_store,
            "first": 20,
            "after": None,
        }
        result = self.client.execute_query(query_string, query_variables)
        return (
            result["dataStoreImports"]["entries"],
            result["dataStoreImports"]["cursor"],
        )

    def get_dataset_import_series(
        self,
        org_id: str,
        data_store: str,
        search: Optional[str] = None,
        first: int = 20,
        cursor: Optional[str] = None,
    ) -> Tuple[List[Dict[str, str]], str]:
        """Get data store imports."""
        query_string = """
            query DataStoreImportSeries($orgId: UUID!, $dataStore: String!, $first: Int, $after: String, $search: String) {
                dataStoreImportSeries(orgId: $orgId, dataStore: $dataStore, first: $first, after: $after, search: $search) {
                    entries {
                        orgId
                        datastore
                        importId
                        seriesId
                        createdAt
                        createdBy
                        totalSize
                        numFiles
                        patientHeaders
                        studyHeaders
                        seriesHeaders
                        url
                    }
                    cursor
                }
            }
        """
        query_variables = {
            "orgId": org_id,
            "dataStore": data_store,
            "first": first,
            "after": cursor,
            "search": search,
        }
        result = self.client.execute_query(query_string, query_variables)
        return (
            result["dataStoreImportSeries"]["entries"],
            result["dataStoreImportSeries"]["cursor"],
        )

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

    def get_datapoint_latest(
        self,
        org_id: str,
        project_id: str,
        task_id: str,
        presign_items: bool = False,
        with_consensus: bool = False,
    ) -> Dict:
        """Get the latest datapoint."""
        query_string = f"""
        query taskSDK($orgId: UUID!, $projectId: UUID!, $taskId: UUID!) {{
            task(orgId: $orgId, projectId: $projectId, taskId: $taskId) {{
                {task_shard(presign_items, with_consensus)}
            }}
        }}
        """
        # EXECUTE THE QUERY
        query_variables = {"orgId": org_id, "projectId": project_id, "taskId": task_id}

        result = self.client.execute_query(query_string, query_variables)

        return result["task"]

    def get_datapoints_latest(
        self,
        org_id: str,
        project_id: str,
        stage_name: Optional[str] = None,
        cache_time: Optional[datetime] = None,
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
            $first: Int
            $after: String
        ) {{
            tasksPaged(
                orgId: $orgId
                projectId: $projectId
                stageName: $stageName
                cacheTime: $cacheTime
                first: $first
                after: $after
            ) {{
                entries {{
                    {task_shard(presign_items, with_consensus)}
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
            "first": first,
            "after": cursor,
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

    def task_search(
        self,
        org_id: str,
        project_id: str,
        stage_name: Optional[str] = None,
        task_search: Optional[str] = None,
        manual_labeling_filters: Optional[TaskFilterParams] = None,
        only_meta_data: bool = True,
        first: int = 50,
        after: Optional[str] = None,
    ) -> Tuple[List[Dict], Optional[str]]:
        """Task search."""
        query_string = f"""
        query tasksListSDK(
            $orgId: UUID!
            $projectId: UUID!
            $stageName: String
            $taskSearch: String
            $manualLabelingFilters: TasksFilter
            $first: Int
            $after: String
        ) {{
            genericTasks(
                orgId: $orgId
                projectId: $projectId
                stageName: $stageName
                taskSearch: $taskSearch
                manualLabelingFilters: $manualLabelingFilters
                first: $first
                after: $after
            ) {{
                entries {{
                    taskId
                    currentStageName
                    createdAt
                    updatedAt
                    priority
                    datapoint {{
                        {datapoint_shard(not only_meta_data, not only_meta_data)}
                    }}
                    currentStageSubTask {{
                        ... on LabelingTask {{
                            assignedTo {{
                                userId
                            }}
                            state
                            assignedAt
                            progressSavedAt
                            completedAt
                            completionTimeMs
                            subTasks {{
                                assignedTo {{
                                    userId
                                }}
                                state
                                assignedAt
                                progressSavedAt
                                completedAt
                                completionTimeMs
                            }}
                        }}
                    }}
                }}
                cursor
            }}
        }}
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
        query presignItemsSDK(
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

    def task_events(
        self,
        org_id: str,
        project_id: str,
        task_id: Optional[str] = None,
        stage_name: Optional[str] = None,
        cache_time: Optional[datetime] = None,
        with_labels: bool = False,
        first: int = 10,
        after: Optional[str] = None,
    ) -> Tuple[List[Dict], Optional[str]]:
        """Get task events."""
        query_variables: Dict[str, Any]
        if task_id:
            query_string = f"""
            query taskSDK($orgId: UUID!, $projectId: UUID!, $taskId: UUID!) {{
                task(orgId: $orgId, projectId: $projectId, taskId: $taskId) {{
                    {router_task_shard(with_labels)}
                }}
            }}
            """
            query_variables = {
                "orgId": org_id,
                "projectId": project_id,
                "taskId": task_id,
            }

            result = self.client.execute_query(query_string, query_variables, True)
            task = result.get("task") or {}
            return [task] if task else [], None

        query_string = f"""
        query taskEventsSDK(
            $orgId: UUID!
            $projectId: UUID!
            $stageName: String
            $cacheTime: DateTime
            $first: Int
            $after: String
        ) {{
            tasksPaged(
                orgId: $orgId
                projectId: $projectId
                stageName: $stageName
                cacheTime: $cacheTime
                first: $first
                after: $after
            ) {{
                entries {{
                    {router_task_shard(with_labels)}
                }}
                cursor
            }}
        }}
        """

        query_variables = {
            "orgId": org_id,
            "projectId": project_id,
            "stageName": stage_name,
            "cacheTime": None if cache_time is None else cache_time.isoformat(),
            "first": first,
            "after": after,
        }

        result = self.client.execute_query(query_string, query_variables, False)
        task_events = result.get("tasksPaged") or {}
        entries: List[Dict] = task_events.get("entries") or []
        return entries, task_events.get("cursor")

    def active_time(
        self,
        org_id: str,
        project_id: str,
        stage_name: str,
        task_id: Optional[str] = None,
        first: int = 100,
        after: Optional[str] = None,
    ) -> Tuple[List[Dict], Optional[str]]:
        """Get task active time."""
        query_string = """
        query taskActiveTimeSDK(
            $orgId: UUID!
            $projectId: UUID!
            $stageName: String!
            $taskId: UUID
            $first: Int
            $after: String
        ) {
            taskActiveTime(
                orgId: $orgId
                projectId: $projectId
                stageName: $stageName
                taskId: $taskId
                first: $first
                after: $after
            ) {
                entries {
                    taskId
                    user {
                        userId
                    }
                    timeSpent
                    cycle
                    date
                }
                cursor
            }
        }
        """

        query_variables = {
            "orgId": org_id,
            "projectId": project_id,
            "stageName": stage_name,
            "taskId": task_id,
            "first": first,
            "after": after,
        }

        result = self.client.execute_query(query_string, query_variables, False)
        task_times = result.get("taskActiveTime", {}) or {}
        entries: List[Dict] = task_times.get("entries", []) or []
        return entries, task_times.get("cursor")
