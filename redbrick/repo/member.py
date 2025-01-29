"""Handlers to access APIs for member."""

from typing import Dict, List

from redbrick.common.client import RBClient
from redbrick.common.member import MemberControllerInterface
from redbrick.repo.shards import ORG_MEMBER_SHARD


class MemberRepo(MemberControllerInterface):
    """Class to manage interaction with member APIs."""

    def __init__(self, client: RBClient) -> None:
        """Construct MemberRepo."""
        self.client = client

    def list_org_members(self, org_id: str) -> List[Dict]:
        """Get a list of all org members."""
        query_string = f"""
        query membersSDK(
            $orgId: UUID!
        ) {{
            members(
                orgId: $orgId
            ) {{
                {ORG_MEMBER_SHARD}
            }}
        }}
        """
        query_variables = {"orgId": org_id}
        result = self.client.execute_query(query_string, query_variables)
        members: List[Dict] = result["members"]
        return members

    def list_project_members(self, org_id: str, project_id: str) -> List[Dict]:
        """Get a list of all project members."""
        query_string = f"""
        query projectMembersSDK(
            $orgId: UUID!
            $projectId: UUID!
        ) {{
            projectMembers(
                orgId: $orgId
                projectId: $projectId
            ) {{
                member {{
                    {ORG_MEMBER_SHARD}
                }}
                role
                stageAccess {{
                    stageName
                    access
                }}
            }}
        }}
        """
        query_variables = {"orgId": org_id, "projectId": project_id}
        result = self.client.execute_query(query_string, query_variables)
        members: List[Dict] = result["projectMembers"]
        return members

    def update_project_memberships(
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

    def remove_project_members(
        self, org_id: str, project_id: str, user_ids: List[str]
    ) -> None:
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
