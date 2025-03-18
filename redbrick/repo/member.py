"""Handlers to access APIs for member."""

from typing import Dict, List

from redbrick.common.client import RBClient
from redbrick.common.member import MemberRepo
from redbrick.repo.shards import ORG_INVITE_SHARD, ORG_MEMBER_SHARD


class MemberRepoImpl(MemberRepo):
    """Class to manage interaction with member APIs."""

    def __init__(self, client: RBClient) -> None:
        """Construct MemberRepoImpl."""
        self.client = client

    def list_org_members(self, org_id: str, active: bool = True) -> List[Dict]:
        """Get a list of all org members."""
        query_string = f"""
        query membersSDK(
            $orgId: UUID!
            $onlyActive: Boolean
        ) {{
            members(
                orgId: $orgId
                onlyActive: $onlyActive
            ) {{
                {ORG_MEMBER_SHARD}
            }}
        }}
        """
        query_variables = {"orgId": org_id, "onlyActive": active}
        result = self.client.execute_query(query_string, query_variables)
        members: List[Dict] = result["members"]
        return members

    def toggle_org_members_status(
        self, org_id: str, user_ids: List[str], active: bool
    ) -> None:
        """Toggle org members status."""
        query_string = """
        mutation toggleMembersStatusSDK(
            $orgId: UUID!
            $userIds: [CustomUUID!]!
            $active: Boolean!
        ) {
            toggleMembersStatus(
                orgId: $orgId
                userIds: $userIds
                active: $active
            ) {
                ok
            }
        }
        """
        query_variables = {"orgId": org_id, "userIds": user_ids, "active": active}
        self.client.execute_query(query_string, query_variables)

    def list_org_invites(self, org_id: str) -> List[Dict]:
        """Get a list of all org invites."""
        query_string = f"""
        query invitesSDK(
            $orgId: UUID!
        ) {{
            invites(
                orgId: $orgId
            ) {{
                {ORG_INVITE_SHARD}
            }}
        }}
        """
        query_variables = {"orgId": org_id}
        result = self.client.execute_query(query_string, query_variables)
        invites: List[Dict] = result["invites"]
        return invites

    def invite_org_user(self, org_id: str, invitation: Dict) -> Dict:
        """Invite an user to the organization."""
        query_string = f"""
        mutation createInviteSDK(
            $orgId: UUID!
            $email: String!
            $role: ROLES!
            $idProvider: IDProvider
        ) {{
            createInvite(
                orgId: $orgId
                email: $email
                role: $role
                idProvider: $idProvider
            ) {{
                ok
                invite {{
                    {ORG_INVITE_SHARD}
                }}
            }}
        }}
        """
        query_variables = {
            "orgId": org_id,
            "email": invitation["email"],
            "role": invitation["role"],
            "idProvider": invitation["idProvider"],
        }
        result = self.client.execute_query(query_string, query_variables)
        return result["createInvite"]["invite"]

    def delete_org_invitation(self, org_id: str, invitation: Dict) -> None:
        """Delete an org invitation."""
        query_string = """
        mutation removeInviteSDK(
            $orgId: UUID!
            $email: String!
            $idProvider: IDProvider
        ) {
            removeInvite(
                orgId: $orgId
                email: $email
                idProvider: $idProvider
            ) {
                ok
            }
        }
        """
        query_variables = {
            "orgId": org_id,
            "email": invitation["email"],
            "idProvider": invitation["idProvider"],
        }
        self.client.execute_query(query_string, query_variables)

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
        self.client.execute_query(query_string, query_variables)
