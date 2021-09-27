from typing import Optional, List, Dict, Tuple
from redbrick.common.export import ExportControllerInterface
from redbrick.common.client import RBClient
from .shards import LABEL_SHARD


LATEST_HISTORY_SHARD = (
    """history(latest: true) {
                    taskData {
                    dataPoint {
                        dpId
                        name
                        itemsPresigned: items(presigned: true)
                        items(presigned: false)
                    }
                    createdByEmail
                    labels(interpolate: true) {
                        %s
                    }
                    }
                }"""
    % LABEL_SHARD
)


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
        query_string = """
        query ($orgId: UUID!, $name: String!){
            customGroup(orgId: $orgId, name:$name){
                dataType
                taskType
                datapointCount
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
        presign: bool = False,
        cursor: Optional[str] = None,
    ) -> Tuple[List[Dict], Optional[str]]:
        """Get datapoints that have made it to the output of the project."""
        query_string = (
            """
        query ($orgId: UUID!, $name: String!,$first: Int, $cursor: String){
        customGroup(orgId: $orgId, name:$name){
            datapointsPaged(first:$first, after:$cursor) {
            entries {
                dpId
                name
                itemsPresigned:items (presigned:true)
                items(presigned:false)
                labelData(customGroupName: $name){
                createdByEmail
                labels(interpolate: true) {
                    %s
                    }
                }


            }
            cursor
            }
        }
        }

        """
            % LABEL_SHARD
        )
        # EXECUTE THE QUERY
        query_variables = {
            "orgId": org_id,
            "name": project_id + "-output",
            "cursor": cursor,
            "first": first,
        }

        result = self.client.execute_query(query_string, query_variables)

        return (
            result["customGroup"]["datapointsPaged"]["entries"],
            result["customGroup"]["datapointsPaged"]["cursor"],
        )

    def datapoints_in_project(self, org_id: str, project_id: str) -> int:
        """Get number of datapoints in project."""
        query_string = """
        query($orgId: UUID!, $projectId: UUID!) {
            tasksPaged(
                orgId: $orgId
                projectId: $projectId
            ) {
                count
            }
        }
        """
        # EXECUTE THE QUERY
        query_variables = {
            "orgId": org_id,
            "projectId": project_id,
        }

        result = self.client.execute_query(query_string, query_variables)

        return int(result["tasksPaged"]["count"])

    def get_datapoints_latest(
        self,
        org_id: str,
        project_id: str,
        first: int = 50,
        presign: bool = False,
        cursor: Optional[str] = None,
    ) -> Tuple[List[Dict], Optional[str]]:
        """Get the latest datapoints."""
        query_string = (
            """
        query($orgId: UUID!, $projectId: UUID!, $first: Int, $cursor: String) {
            tasksPaged(
                orgId: $orgId
                projectId: $projectId
                first: $first
                after: $cursor
            ) {
                entries {
                    %s
                }
                cursor
            }
            }
        """
            % LATEST_HISTORY_SHARD
        )
        # EXECUTE THE QUERY
        query_variables = {
            "orgId": org_id,
            "projectId": project_id,
            "cursor": cursor,
            "first": first,
        }

        result = self.client.execute_query(query_string, query_variables)

        return (
            result["tasksPaged"]["entries"],
            result["tasksPaged"]["cursor"],
        )

    def get_datapoint_latest(self, org_id: str, project_id: str, task_id: str) -> Dict:
        """Get the latest labels for a single datapoint."""
        query_string = (
            """
        query($orgId: UUID!, $projectId: UUID!, $taskId: UUID!) {
            task(
                orgId: $orgId
                projectId: $projectId
                taskId: $taskId

            ) {
                %s
            }
            }
        """
            % LATEST_HISTORY_SHARD
        )
        # EXECUTE THE QUERY
        query_variables = {
            "orgId": org_id,
            "projectId": project_id,
            "taskId": task_id,
        }

        result: Dict[str, Dict] = self.client.execute_query(
            query_string, query_variables
        )

        return result["task"]
