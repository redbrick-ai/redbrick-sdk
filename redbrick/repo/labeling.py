"""Abstract interface to Labeling APIs."""
from typing import Optional, List, Dict
import aiohttp

from redbrick.common.client import RBClient
from redbrick.common.labeling import LabelingControllerInterface


class LabelingRepo(LabelingControllerInterface):
    """Implementation of manual labeling apis."""

    def __init__(self, client: RBClient) -> None:
        """Construct ExportRepo."""
        self.client = client

    def get_labeling_tasks(
        self, org_id: str, project_id: str, stage_name: str, count: int = 5
    ) -> List[Dict]:
        """Get labeling tasks."""
        query = """
        mutation assignLabelingTasks(
            $orgId: UUID!
            $projectId: UUID!
            $stageName: String!
            $count: Int!
        )  {
                assignLabelingTasks(
                orgId: $orgId
                projectId: $projectId
                stageName: $stageName
                count: $count
                ) {
                    orgId
                    projectId
                    stageName
                    state
                    taskId
                    taskType
                    completionTimeMs
                    progressSavedAt
                    assignedTo {
                        userId
                        loggedInUser
                    }
                    taxonomy {
                        name
                        version
                    }
                    datapoint {
                        itemsPresigned: items(presigned: true)
                        items(presigned: false)
                        dataType
                        name
                    }
                    taskData {
                        subName
                        taskType
                        createdAt
                        createdBy
                        labelsData(interpolate: true)
                }
            }
        }
        """

        response = self.client.execute_query(
            query,
            {
                "orgId": org_id,
                "projectId": project_id,
                "stageName": stage_name,
                "count": count,
            },
        )
        tasks: List[Dict] = response["assignLabelingTasks"]
        return tasks

    async def presign_labels_path(
        self,
        session: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        task_id: str,
        file_type: str,
    ) -> Dict:
        """Presign labels path."""
        query = """
        query presignLabelsPathSDK(
            $orgId: UUID!
            $projectId: UUID!
            $taskId: UUID!
            $fileType: String!
        ) {
            presignLabelsPath(
                orgId: $orgId
                projectId: $projectId
                taskId: $taskId
                fileType: $fileType
            ) {
                fileName
                filePath
                presignedUrl
            }
        }
        """
        variables = {
            "orgId": org_id,
            "projectId": project_id,
            "taskId": task_id,
            "fileType": file_type,
        }
        response = await self.client.execute_query_async(session, query, variables)
        presigned: Dict = response["presignLabelsPath"]
        return presigned

    async def put_labeling_results(
        self,
        session: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        stage_name: str,
        task_id: str,
        labels_data: str,
        labels_map: Optional[List[Dict]] = None,
        finished: bool = True,
    ) -> None:
        """Put Labeling results."""
        query = """
        mutation putTaskAndLabels(
            $orgId: UUID!
            $projectId: UUID!
            $stageName: String!
            $taskId: UUID!
            $elapsedTimeMs: Int!
            $finished: Boolean!
            $labelsData: String
            $labelsMap: [LabelMapInput!]
        ) {
            putManualLabelingTaskAndLabels(
                orgId: $orgId
                projectId: $projectId
                stageName: $stageName
                taskId: $taskId
                elapsedTimeMs: $elapsedTimeMs
                finished: $finished
                labelsData: $labelsData
                labelsMap: $labelsMap
            ) {
                ok
            }
        }
        """

        variables = {
            "orgId": org_id,
            "projectId": project_id,
            "stageName": stage_name,
            "taskId": task_id,
            "labelsData": labels_data,
            "labelsMap": labels_map,
            "finished": finished,
            "elapsedTimeMs": 0,
        }
        await self.client.execute_query_async(session, query, variables)

    async def put_labeling_task_result(
        self,
        session: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        stage_name: str,
        task_id: str,
    ) -> None:
        """Put labeling result for task."""
        query = """
        mutation putLabelingTask(
            $orgId: UUID!
            $projectId: UUID!
            $stageName: String!
            $taskId: UUID!
        ) {
            putManualLabelingTask(
                orgId: $orgId
                projectId: $projectId
                stageName: $stageName
                taskId: $taskId
            ) {
                ok
            }
        }
        """

        variables = {
            "orgId": org_id,
            "projectId": project_id,
            "stageName": stage_name,
            "taskId": task_id,
        }
        await self.client.execute_query_async(session, query, variables)

    async def put_review_task_result(
        self,
        session: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        stage_name: str,
        task_id: str,
        review_val: bool,
    ) -> None:
        """Put review result for task."""
        query = """
        mutation putReviewTask(
            $orgId: UUID!
            $projectId: UUID!
            $stageName: String!
            $reviewVal: Boolean!
            $taskId: UUID!
            $elapsedTimeMs: Int!
        ) {
            putExpertReviewTask(
            orgId: $orgId
            projectId: $projectId
            stageName: $stageName
            reviewVal: $reviewVal
            taskId: $taskId
            elapsedTimeMs: $elapsedTimeMs
            ) {
            ok
            }
        }
        """

        variables = {
            "orgId": org_id,
            "projectId": project_id,
            "stageName": stage_name,
            "taskId": task_id,
            "reviewVal": review_val,
            "elapsedTimeMs": 0,
        }

        await self.client.execute_query_async(session, query, variables)

    def assign_tasks(
        self,
        org_id: str,
        project_id: str,
        task_ids: List[str],
        emails: Optional[List[str]] = None,
        current_user: bool = False,
        refresh: bool = True,
    ) -> List[Dict]:
        """Assign tasks to specified email or current API key."""
        query_string = """
        mutation assignTasksMultipleUsers(
            $orgId: UUID!
            $projectId: UUID!
            $taskIds: [UUID!]!
            $emails: [String!]
            $currentUser: Boolean
            $refresh: Boolean
        ) {
            assignTasksMultipleUsers(
                orgId: $orgId
                projectId: $projectId
                taskIds: $taskIds
                emails: $emails
                currentUser: $currentUser
                refresh: $refresh
            ) {
                taskId
                name
                stageName
            }
        }
        """

        # EXECUTE THE QUERY
        query_variables = {
            "orgId": org_id,
            "projectId": project_id,
            "taskIds": task_ids,
            "emails": emails,
            "currentUser": current_user,
            "refresh": refresh,
        }

        response = self.client.execute_query(query_string, query_variables)
        tasks: List[Dict] = response["assignTasksMultipleUsers"]
        return tasks

    async def move_task_to_start(
        self,
        session: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        task_id: str,
    ) -> None:
        """Move groundtruth task back to start."""
        query = """
        mutation moveTaskToStart(
            $orgId: UUID!
            $projectId: UUID!
            $taskId: UUID!
        ) {
            moveTaskToStart(
                orgId: $orgId
                projectId: $projectId
                taskId: $taskId
            ) {
                ok
            }
        }
        """

        variables = {"orgId": org_id, "projectId": project_id, "taskId": task_id}

        await self.client.execute_query_async(session, query, variables)
