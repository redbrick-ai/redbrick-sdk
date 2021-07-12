"""Abstract interface to active learning API."""


from typing import Optional, List, Dict, Tuple

import aiohttp

from redbrick.common.client import RBClient
from redbrick.common.learning import LearningControllerInterface


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
        print(result)
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
                            dpId
                            name
                            itemsPresigned:items (presigned:true)
                            items(presigned:false)
                        }
                        groundTruth {
                            labels {
                                category
                                attributes {
                                    ... on LabelAttributeInt {
                                    name
                                    valint: value
                                    }
                                    ... on LabelAttributeBool {
                                    name
                                    valbool: value
                                    }
                                    ... on LabelAttributeFloat {
                                    name
                                    valfloat: value
                                    }
                                    ... on LabelAttributeString {
                                    name
                                    valstr: value
                                    }
                                }
                                labelid
                                frameindex
                                trackid
                                keyframe
                                taskclassify
                                frameclassify
                                end
                                bbox2d {
                                    xnorm
                                    ynorm
                                    wnorm
                                    hnorm
                                }
                                point {
                                    xnorm
                                    ynorm
                                }
                                polyline {
                                    xnorm
                                    ynorm
                                }
                                polygon {
                                    xnorm
                                    ynorm
                                }
                                pixel {
                                    imagesize
                                    regions
                                    holes
                                }
                                ellipse {
                                    xcenternorm
                                    ycenternorm
                                    xnorm
                                    ynorm
                                    rot
                                }
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
        query = """
        query  ($orgId:UUID!, $projectId:UUID!, $stageName: String!){
            activeLearningClientSummary(orgId:$orgId, projectId:$projectId, stageName: $stageName){
                tdType
                taxonomy {
                    name
                    version
                    categories {
                        name
                        children {
                            name
                            classId
                            children {
                                name
                                classId
                                children {
                                    name
                                    classId
                                }
                            }
                        }
                    }
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
