"""Abstract interface to active learning API."""


from typing import Optional, List, Dict, Tuple

import aiohttp

from redbrick.common.client import RBClient
from redbrick.common.learning import (
    LearningControllerInterface,
    LearningController2Interface,
)

from .shards import TAXONOMY_SHARD


class LearningRepo(LearningControllerInterface):
    """Abstract interface to Active Learning APIs."""

    def __init__(self, client: RBClient) -> None:
        """Construct ExportRepo."""
        self.client = client

    def check_for_job(
        self, org_id: str, project_id: str, stage_name: str
    ) -> Optional[int]:
        """Check for a job, returns cycle number."""
        query = """
        query  ($orgId:UUID!, $projectId:UUID!, $stageName: String!){
            activeLearningClientSummary(orgId:$orgId, projectId:$projectId, stageName: $stageName){
                availableJob {
                    cycleStatus
                    cycle
                }
            }
        }
        """
        variables = {
            "orgId": org_id,
            "projectId": project_id,
            "stageName": stage_name,
        }
        result = self.client.execute_query(query, variables)

        if result.get("activeLearningClientSummary", {}).get("availableJob"):
            return int(result["activeLearningClientSummary"]["availableJob"]["cycle"])

        return None

    def get_batch_of_tasks(
        self,
        org_id: str,
        project_id: str,
        stage_name: str,
        first: int = 50,
        cursor: Optional[str] = None,
    ) -> Tuple[List[dict], Optional[str]]:
        """Get batch of tasks, paginated."""
        query = """
        query  ($orgId:UUID!, $projectId:UUID!, $stageName: String!, $first: Int!, $cursor: String){
            activeLearningClientSummary(orgId:$orgId, projectId:$projectId, stageName: $stageName){
                tdType
                tasks (cursor: $cursor, first: $first){
                    cursor
                    entries {
                        taskId
                        datapoint {
                            name
                            itemsPresigned:items (presigned:true)
                            items(presigned:false)
                        }
                        groundTruth {
                            labelsData(interpolate: true) {
                                %s
                            }
                        }
                    }
                }
            }
        }
        """
        variables = {
            "cursor": cursor,
            "orgId": org_id,
            "projectId": project_id,
            "stageName": stage_name,
            "first": 100,
        }
        result = self.client.execute_query(query, variables)
        return (
            result["activeLearningClientSummary"]["tasks"]["entries"],
            result["activeLearningClientSummary"]["tasks"]["cursor"],
        )

    def get_taxonomy_and_type(
        self, org_id: str, project_id: str, stage_name: str
    ) -> Tuple[dict, str]:
        """Get the taxonomy for active learning."""
        query = (
            """
        query  ($orgId:UUID!, $projectId:UUID!, $stageName: String!){
            activeLearningClientSummary(orgId:$orgId, projectId:$projectId, stageName: $stageName){
                tdType
                taxonomy {
                    %s
                }
            }
        }
        """
            % TAXONOMY_SHARD
        )
        variables = {
            "orgId": org_id,
            "projectId": project_id,
            "stageName": stage_name,
        }
        result = self.client.execute_query(query, variables)

        return (
            result["activeLearningClientSummary"]["taxonomy"],
            result["activeLearningClientSummary"]["tdType"],
        )

    def send_batch_learning_results(
        self,
        org_id: str,
        project_id: str,
        stage_name: str,
        cycle: int,
        tasks: List[Dict],
    ) -> None:
        """
        Send a batch of learning results.

        tasks is a list of dictionaries containing the following keys:
        {
            "taskId": "<>",
            "score": [0,1],
            "labels": [{ }]  // see standard label format
        }
        """
        raise NotImplementedError()

    async def send_batch_learning_results_async(
        self,
        aio_client: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        stage_name: str,
        cycle: int,
        tasks: List[Dict],
    ) -> None:
        """Perform send_batch_learning_results with asyncio."""
        query = """
        mutation(
            $orgId: UUID!
            $projectId: UUID!
            $stageName: String!
            $tasks: [AlTaskLabelsInput!]!
            $cycle: Int!
        ) {
            sendAlLabels(
                orgId: $orgId
                projectId: $projectId
                stageName: $stageName
                tasks: $tasks
                cycle: $cycle
            ) {
                ok
            }
        }
        """
        variables = {
            "orgId": org_id,
            "projectId": project_id,
            "stageName": stage_name,
            "cycle": cycle,
            "tasks": tasks,
        }
        await self.client.execute_query_async(aio_client, query, variables)

    def set_cycle_status(
        self,
        org_id: str,
        project_id: str,
        stage_name: str,
        cycle: int,
        cycle_status: str,
    ) -> None:
        """Set status of current training cycle."""
        query = """
        mutation(
            $orgId: UUID!
            $projectId: UUID!
            $stageName: String!
            $cycle: Int!,
            $status: CycleStatus!
        ) {
            updateAlCycleStatus(
                orgId: $orgId
                projectId: $projectId
                stageName: $stageName
                cycle: $cycle
                cycleStatus: $status
            ) {
                ok
            }
        }
        """

        variables = {
            "orgId": org_id,
            "projectId": project_id,
            "stageName": stage_name,
            "cycle": cycle,
            "status": cycle_status,
        }
        self.client.execute_query(query, variables)


class Learning2Repo(LearningController2Interface):
    """Abstract interface to Active Learning APIs."""

    def __init__(self, client: RBClient) -> None:
        """Construct ExportRepo."""
        self.client = client

    def check_for_job(self, org_id: str, project_id: str) -> Dict:
        """Check for a job, and num new tasks."""
        query = """
        query checkForJob ($orgId:UUID!, $projectId: UUID!) {
            currentCycleTracker(orgId:$orgId, projectId:$projectId) {
                newTasks
                newTasksProcessing
                isProcessing
            }
        }
        """
        variables = {"orgId": org_id, "projectId": project_id}
        result: Dict[str, Dict] = self.client.execute_query(query, variables)

        return result["currentCycleTracker"]

    def get_taxonomy_and_type(self, org_id: str, project_id: str) -> Tuple[dict, str]:
        """Get the taxonomy for active learning."""
        query = (
            """
        query projectTypeAndTaxonomy ($orgId: UUID!, $projectId: UUID!) {
            project(orgId: $orgId, projectId: $projectId){
                tdType
                taxonomy {
                    %s
                }
            }
        }

        """
            % TAXONOMY_SHARD
        )

        variables = {"orgId": org_id, "projectId": project_id}
        result: Dict = self.client.execute_query(query, variables)
        return (
            result["project"]["taxonomy"],
            result["project"]["tdType"],
        )

    async def update_prelabels_and_priorities(
        self,
        aio_client: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        stage_name: str,
        tasks: List[Dict],
    ) -> None:
        """
        Perform send_batch_learning_results with asyncio.

        tasks is a list of dictionaries containing the following keys:
        {
            "taskId": "<>",
            "priority": [0,1],
            "labels": [{ }]  // see standard label format
        }
        """
        query = """
        mutation updatePrelabelsAndPriorities(
            $orgId: UUID!
            $projectId: UUID!
            $stageName: String!
            $tasks: [TaskUpdateInput!]!
        ) {
            updatePrelabelsOrPriority(
                orgId: $orgId
                projectId: $projectId
                stageName: $stageName
                tasks: $tasks
            ) {
                ok
            }
        }
        """
        variables = {
            "orgId": org_id,
            "projectId": project_id,
            "stageName": stage_name,
            "tasks": tasks,
        }

        await self.client.execute_query_async(aio_client, query, variables)

    def start_processing(self, org_id: str, project_id: str) -> None:
        """Set status of current training cycle."""
        query = """
        mutation ($orgId:UUID!, $projectId:UUID!){
            startCycleProcessing(orgId:$orgId, projectId:$projectId){
                ok
            }
        }
        """
        variables = {"orgId": org_id, "projectId": project_id}
        self.client.execute_query(query, variables)

    def end_processing(self, org_id: str, project_id: str) -> None:
        """Set status of current training cycle."""
        query = """
        mutation ($orgId:UUID!, $projectId:UUID!){
            endCycleProcessing(orgId:$orgId, projectId:$projectId){
                ok
            }
        }
        """
        variables = {"orgId": org_id, "projectId": project_id}
        self.client.execute_query(query, variables)
