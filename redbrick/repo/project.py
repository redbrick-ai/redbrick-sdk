"""Handlers to access APIs for getting projects."""

from typing import List, Dict

from redbrick.common.client import RBClient
from redbrick.common.project import ProjectRepoInterface


class ProjectRepo(ProjectRepoInterface):
    """Class to manage interaction with project APIs."""

    def __init__(self, client: RBClient) -> None:
        """Construct ProjectRepo."""
        self.client = client

    def get_project_name(self, org_id: str, project_id: str) -> str:
        """
        Get project name.

        Raise an exception if project does not exist.
        """
        query = """
            query sdkGetProjectName($orgId: UUID!, $projectId: UUID!){
                project(orgId: $orgId, projectId: $projectId){
                    name
                }
            }
        """
        variables = {"orgId": org_id, "projectId": project_id}
        response = self.client.execute_query(query, variables)
        if response.get("project", {}).get("name"):
            name: str = response["project"]["name"]
            return name
        print(response)
        raise Exception("Project does not exist")

    def get_stages(self, org_id: str, project_id: str) -> List[Dict]:
        """Get stages."""
        query = """
            query sdkGetStages($orgId: UUID!, $projectId: UUID!){
                stages(orgId: $orgId, projectId: $projectId){
                    stageName
                    brickName
                }
            }
        """
        variables = {"orgId": org_id, "projectId": project_id}
        response: Dict[str, List[Dict]] = self.client.execute_query(query, variables)
        return response["stages"]
