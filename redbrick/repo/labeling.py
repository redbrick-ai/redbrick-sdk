"""Abstract interface to Labeling APIs."""

from typing import Optional, List, Dict, Tuple
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

    async def put_labeling_results(
        self,
        session: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        stage_name: str,
        task_id: str,
        labels_data: str,
    ) -> None:
        """Put Labeling results."""
        query = """
        mutation putTaskAndLabels(
        $orgId: UUID!
        $projectId: UUID!
        $stageName: String!
        $taskId: UUID!
        $elapsedTimeMs: Int!
        $labelsData: String
        $finished: Boolean!
        ) {
            putManualLabelingTaskAndLabels(
                orgId: $orgId
                projectId: $projectId
                stageName: $stageName
                taskId: $taskId
                elapsedTimeMs: $elapsedTimeMs
                labelsData: $labelsData
                finished: $finished
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
            "finished": True,
            "elapsedTimeMs": 0,
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

    def assign_task(
        self, org_id: str, project_id: str, stage_name: str, task_id: str, email: str
    ) -> None:
        """Assign task to specified email."""
        query_string = """
        mutation assignTaskByEmailSDK(
            $orgId: UUID!,
            $projectId: UUID!,
            $stageName: String!,
            $taskId: UUID!,
            $email: String!
        ){
            assignTask(
                orgId: $orgId
                projectId: $projectId
                stageName: $stageName
                taskId: $taskId
                email: $email
            ) {
                task {
                    taskId
                }
            }
        }
        """

        # EXECUTE THE QUERY
        query_variables = {
            "orgId": org_id,
            "projectId": project_id,
            "stageName": stage_name,
            "taskId": task_id,
            "email": email,
        }

        self.client.execute_query(query_string, query_variables)

    def get_tasks_queue(
        self,
        org_id: str,
        project_id: str,
        stage_name: str,
        first: int,
        cursor: Optional[str] = None,
    ) -> Tuple[List[Dict], str]:
        """Get task queue."""
        query_string = """
            query(
                $orgId: UUID!
                $projectId: UUID!
                $stageName: String!
                $first: Int!
                $after: String
                ) {
                taskQueue(
                    orgId: $orgId
                    projectId: $projectId
                    stageName: $stageName
                    first: $first
                    after: $after
                ) {
                    cursor
                    entries {
                        taskId
                        state
                        assignedTo {
                            email
                            userId
                        }
                        datapoint {
                            itemsPresigned: items(presigned: true)
                            items(presigned: false)
                            dataType
                            name
                    }
                    }
                }
            }

        """

        # EXECUTE THE QUERY
        query_variables = {
            "orgId": org_id,
            "projectId": project_id,
            "stageName": stage_name,
            "first": first,
            "after": cursor,
        }

        response = self.client.execute_query(query_string, query_variables)
        return response["taskQueue"]["entries"], response["taskQueue"]["cursor"]

    def get_task_queue_count(
        self,
        org_id: str,
        project_id: str,
        stage_name: str,
        for_active_learning: bool = False,
    ) -> int:
        """Get the length of the task queue for showing loading."""
        query_string = """
            query ($orgId: UUID!
                $projectId: UUID!
                $stageName: String!)  {
                manualLabelingStageSummary(
                    orgId:$orgId,
                    projectId:$projectId,
                    stageName:$stageName
                ){
                    taskStatusSummary {
                    assignedCount
                    unassignedCount
                    inProgressCount
                    }
                }
            }
        """
        # EXECUTE THE QUERY
        query_variables = {
            "orgId": org_id,
            "projectId": project_id,
            "stageName": stage_name,
        }

        response = self.client.execute_query(query_string, query_variables)
        summary = response["manualLabelingStageSummary"]["taskStatusSummary"]
        return (
            int(summary["unassignedCount"])
            if for_active_learning
            else int(
                summary["assignedCount"]
                + summary["unassignedCount"]
                + summary["inProgressCount"]
            )
        )
