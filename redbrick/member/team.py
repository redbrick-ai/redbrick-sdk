"""Public interface to team controller."""

from typing import List

from redbrick.common.entities import RBOrganization
from redbrick.common.member import OrgInvite, OrgMember, Team


class TeamImpl(Team):
    """Primary interface to organization team."""

    def __init__(self, org: RBOrganization) -> None:
        """Construct Member object."""
        self.org = org
        self.context = self.org.context

    def _get_filtered_members(
        self, member_id: str, members: List[OrgMember]
    ) -> List[OrgMember]:
        return [
            member for member in members if member_id in (member.user_id, member.email)
        ]

    def _get_unique_member(self, member_id: str, members: List[OrgMember]) -> OrgMember:
        filtered_members = self._get_filtered_members(member_id, members)

        if not filtered_members:
            raise ValueError(f"Member {member_id} not found")

        if len(filtered_members) > 1:
            raise ValueError(
                f"Multiple members found with ID: {member_id}. Please use unique userId."
            )

        return filtered_members[0]

    def get_member(self, member_id: str) -> OrgMember:
        """Get a team member.

        .. code:: python

            org = redbrick.get_org(org_id, api_key)
            member = org.team.get_member(member_id)

        Parameters
        --------------
        member_id: str
            Unique member userId or email.

        Returns
        -------------
        OrgMember
        """
        members = self.list_members()
        return self._get_unique_member(member_id, members)

    def list_members(self, active: bool = True) -> List[OrgMember]:
        """Get a list of all organization members.

        .. code:: python

            org = redbrick.get_org(org_id, api_key)
            members = org.team.list_members()

        Parameters
        --------------
        active: bool
            Only return active members if True, else return all members.

        Returns
        -------------
        List[OrgMember]
        """
        members = self.context.member.list_org_members(self.org.org_id, active)
        return [OrgMember.from_entity(member) for member in members]

    def disable_members(self, member_ids: List[str]) -> None:
        """Disable organization members.

        .. code:: python

            org = redbrick.get_org(org_id, api_key)
            org.team.disable_members(member_ids)

        Parameters
        --------------
        member_ids: List[str]
            Unique member ids (userId or email).
        """
        members = self.list_members()
        self.context.member.toggle_org_members_status(
            self.org.org_id,
            [
                self._get_unique_member(member_id, members).user_id
                for member_id in member_ids
            ],
            False,
        )

    def enable_members(self, member_ids: List[str]) -> None:
        """Enable organization members.

        .. code:: python

            org = redbrick.get_org(org_id, api_key)
            org.team.enable_members(member_ids)

        Parameters
        --------------
        member_ids: List[str]
            Unique member ids (userId or email).
        """
        members = self.list_members(False)
        members = [member for member in members if not member.is_active]
        self.context.member.toggle_org_members_status(
            self.org.org_id,
            [
                self._get_unique_member(member_id, members).user_id
                for member_id in member_ids
            ],
            True,
        )

    def list_invites(self) -> List[OrgInvite]:
        """Get a list of all pending or declined invites.

        .. code:: python

            org = redbrick.get_org(org_id, api_key)
            members = org.team.list_invites()

        Returns
        -------------
        List[OrgInvite]
        """
        invites = self.context.member.list_org_invites(self.org.org_id)
        return [
            OrgInvite.from_entity(invite)
            for invite in invites
            if invite["state"] in ("PENDING", "DECLINED")
        ]

    def invite_user(self, invitation: OrgInvite) -> OrgInvite:
        """Invite a user to the organization.

        .. code:: python

            org = redbrick.get_org(org_id, api_key)
            invitation = org.team.invite_user(OrgInvite(email="...", role=OrgMember.Role.MEMBER))

        Parameters
        --------------
        invitation: OrgInvite
            Organization invite

        Returns
        -------------
        OrgInvite
        """
        if invitation.status != OrgInvite.Status.PENDING:
            raise ValueError("New invitation must be in PENDING state")

        invite = self.context.member.invite_org_user(
            self.org.org_id, invitation.to_entity()
        )
        return OrgInvite.from_entity(invite)

    def revoke_invitation(self, invitation: OrgInvite) -> None:
        """Revoke org user invitation.

        .. code:: python

            org = redbrick.get_org(org_id, api_key)
            org.team.revoke_invitation(OrgInvite(email="..."))

        Parameters
        --------------
        invitation: OrgInvite
            Organization invite
        """
        if invitation.status == OrgInvite.Status.ACCEPTED:
            raise ValueError("ACCEPTED invitations cannot be deleted")

        self.context.member.delete_org_invitation(
            self.org.org_id, invitation.to_entity()
        )
