"""Abstract interface to exporting."""

from typing import Optional, List, Dict
import aiohttp

from redbrick.common.client import RBClient
from redbrick.common.labeling import LabelingControllerInterface


class LabelingRepo(LabelingControllerInterface):
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
                    dpId
                    thumbnail: items(presigned: true, thumbnail: true)
                    dataType
                    name
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
        print(response)
        tasks: List[Dict] = response["assignLabelingTasks"]
        return tasks

    async def put_labeling_results(
        self,
        session: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        stage_name: str,
        task_id: str,
        labels: List[Dict],
    ) -> None:
        """Put Labeling results."""
        query = """
        mutation putTaskAndLabels(
        $orgId: UUID!
        $projectId: UUID!
        $stageName: String!
        $taskId: UUID!
        $elapsedTimeMs: Int!
        $labels: [LabelInput]!
        $finished: Boolean!
        ) {
            putManualLabelingTaskAndLabels(
                orgId: $orgId
                projectId: $projectId
                stageName: $stageName
                taskId: $taskId
                elapsedTimeMs: $elapsedTimeMs
                labels: $labels
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
            "labels": labels,
            "finished": True,
            "elapsedTimeMs": 0,
        }
        result = await self.client.execute_query_async(session, query, variables)

    def put_review_task_result(
        self,
        org_id: str,
        project_id: str,
        stage_name: str,
        task_id: str,
        review_val: bool,
    ) -> None:
        """Put review result for task."""
