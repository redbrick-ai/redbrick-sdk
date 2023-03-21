"""Handlers to access APIs for getting workspaces."""
from typing import Dict

from redbrick.common.client import RBClient
from redbrick.common.workspace import WorkspaceRepoInterface


class WorkspaceRepo(WorkspaceRepoInterface):
    """Class to manage interaction with workspace APIs."""

    def __init__(self, client: RBClient) -> None:
        """Construct WorkspaceRepo."""
        self.client = client

    def get_workspace(self, org_id: str, workspace_id: str) -> Dict:
        """
        Get workspace name and status.

        Raise an exception if workspace does not exist.
        """
        query = """
            query sdkGetWorkspace($orgId: UUID!, $workspaceId: UUID!){
                workspace(orgId: $orgId, workspaceId: $workspaceId){
                    orgId
                    workspaceId
                    name
                    status
                    createdAt
                }
            }
        """
        variables = {"orgId": org_id, "workspaceId": workspace_id}
        response: Dict[str, Dict] = self.client.execute_query(query, variables)
        if response.get("workspace"):
            return response["workspace"]

        raise Exception("Workspace does not exist")

    def create_workspace(
        self, org_id: str, workspace_name: str, exists_okay: bool = False
    ) -> Dict:
        """
        Create a workspace.

        Raise an exception if workspace already exists.
        """
        query = """
            mutation sdkCreateWorkspace($orgId: UUID!, $workspaceName: String!){
                createWorkspace(orgId: $orgId, workspaceName: $workspaceName){
                    orgId
                    workspaceId
                    name
                }
            }
        """
        variables = {"orgId": org_id, "workspaceName": workspace_name}
        response: Dict[str, Dict] = self.client.execute_query(query, variables)
        if response.get("createWorkspace"):
            return response["createWorkspace"]

        if exists_okay:
            return self.get_workspace(org_id, workspace_name)

        raise Exception("Workspace already exists")
