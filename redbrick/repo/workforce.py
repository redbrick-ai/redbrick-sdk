"""Handlers to access APIs for project workforce."""

from typing import Dict, List

from redbrick.common.client import RBClient
from redbrick.common.workforce import WorkforceControllerInterface


class WorkforceRepo(WorkforceControllerInterface):
    """Class to manage interaction with project workforce APIs."""

    def __init__(self, client: RBClient) -> None:
        """Construct WorkforceRepo."""
        self.client = client

    def org_members(self, org_id: str) -> List[Dict]:
        """Get a list of all org members."""
        query_string = """
        query membersSDK(
            $orgId: UUID!
        ) {
            members(
                orgId: $orgId
            ) {
                user {
                    userId
                    email
                    givenName
                    familyName
                    mfaSetup
                    lastSeen
                    updatedAt
                }
                role
                tags
                lastSeen
            }
        }
        """
        query_variables = {"orgId": org_id}
        result = self.client.execute_query(query_string, query_variables)
        members: List[Dict] = result["members"]
        return members

    def list_members(self, org_id: str, project_id: str) -> List[Dict]:
        """Get a list of all project members."""
        query_string = """
        query projectMembersSDK(
            $orgId: UUID!
            $projectId: UUID!
        ) {
            projectMembers(
                orgId: $orgId
                projectId: $projectId
            ) {
                member {
                    user {
                        userId
                        email
                        givenName
                        familyName
                    }
                    role
                    tags
                }
                role
                stageAccess {
                    stageName
                    access
                }
            }
        }
        """
        query_variables = {"orgId": org_id, "projectId": project_id}
        result = self.client.execute_query(query_string, query_variables)
        members: List[Dict] = result["projectMembers"]
        return members

    def update_memberships(
        self, org_id: str, project_id: str, memberships: List[Dict]
    ) -> None:
        """Update project memberships."""
        query_string = """
        mutation updateProjectMembershipSDK(
            $orgId: UUID!
            $projectId: UUID!
            $memberAccess: [MemberAccessInput!]!
        ) {
            updateProjectMembership(
                orgId: $orgId
                projectId: $projectId
                memberAccess: $memberAccess
            ) {
                ok
            }
        }
        """
        query_variables = {
            "orgId": org_id,
            "projectId": project_id,
            "memberAccess": memberships,
        }
        self.client.execute_query(query_string, query_variables)

    def remove_members(self, org_id: str, project_id: str, user_ids: List[str]) -> None:
        """Remove project members."""
        query_string = """
        mutation removeProjectMembersSDK(
            $orgId: UUID!
            $projectId: UUID!
            $userIds: [CustomUUID!]!
        ) {
            removeProjectMembers(
                orgId: $orgId
                projectId: $projectId
                userIds: $userIds
            ) {
                ok
            }
        }
        """
        query_variables = {
            "orgId": org_id,
            "projectId": project_id,
            "userIds": user_ids,
        }
        print(query_variables)
        self.client.execute_query(query_string, query_variables)
