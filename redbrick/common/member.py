"""Abstract interface to workforce."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from abc import ABC, abstractmethod

from dateutil import parser  # type: ignore


@dataclass
class OrgMember:
    """Organization Member.

    Parameters
    --------------
    user_id: str
        User ID.

    email: str
        User email.

    given_name: str
        User given name.

    family_name: str
        User family name.

    role: OrgMember.Role
        User role in organization.

    tags: List[str]
        Tags associated with the user.

    is_2fa_enabled: bool
        Whether 2FA is enabled for the user.

    is_active: bool
        Whether the user is active.

    last_active: Optional[datetime] = None
        Last time the user was active.

    sso_provider: Optional[str] = None
        User identity SSO provider.
    """

    class Role(str, Enum):
        """Enumerate access levels for Organization.

        - ``OWNER`` - Organization Owner
        - ``ADMIN`` - Organization Admin
        - ``MEMBER`` - Organization Member

        """

        OWNER = "OWNER"
        ADMIN = "ADMIN"
        MEMBER = "MEMBER"

    user_id: str
    email: str
    given_name: str
    family_name: str
    role: "OrgMember.Role"
    tags: List[str]
    is_2fa_enabled: bool
    is_active: bool
    last_active: Optional[datetime] = None
    sso_provider: Optional[str] = None

    @classmethod
    def from_entity(cls, member: Dict) -> "OrgMember":
        """Get object from entity."""
        return cls(
            user_id=member["user"]["userId"],
            email=member["user"]["email"],
            given_name=member["user"]["givenName"],
            family_name=member["user"]["familyName"],
            role=OrgMember.Role(member["role"]),
            tags=member["tags"],
            is_2fa_enabled=bool(member["user"]["mfaSetup"]),
            is_active=bool(member["active"]),
            last_active=(
                parser.parse(member["lastSeen"]) if member.get("lastSeen") else None
            ),
            sso_provider=(
                None
                if member["user"]["idProvider"] in ("COGNITO", "Google")
                else member["user"]["idProvider"].removeprefix("rb-")
            ),
        )


@dataclass
class OrgInvite:
    """Organization Invite.

    Parameters
    --------------
    email: str
        User email.

    role: OrgMember.Role
        User role in organization.

    sso_provider: Optional[str] = None
        User identity SSO provider.

    status: OrgInvite.Status = OrgInvite.Status.PENDING
        Invite status.
    """

    class Status(str, Enum):
        """Enumerate invite status.

        - ``PENDING`` - Pending invitation
        - ``ACCEPTED`` - Accepted invitation
        - ``DECLINED`` - Declined invitation

        """

        PENDING = "PENDING"
        ACCEPTED = "ACCEPTED"
        DECLINED = "DECLINED"

    email: str
    role: OrgMember.Role
    sso_provider: Optional[str] = None
    status: "OrgInvite.Status" = Status.PENDING

    @classmethod
    def from_entity(cls, invite: Dict) -> "OrgInvite":
        """Get object from entity."""
        return cls(
            email=invite["email"],
            role=OrgMember.Role(invite["role"]),
            sso_provider=(
                None
                if invite["idProvider"] in ("COGNITO", "Google")
                else invite["idProvider"].removeprefix("rb-")
            ),
            status=OrgInvite.Status(invite["state"]),
        )

    def to_entity(self) -> Dict:
        """Get entity from object."""
        return {
            "email": self.email,
            "role": self.role.value,
            "idProvider": self.sso_provider,
            "state": self.status.value,
        }


@dataclass
class ProjectMember:
    """Project Member.

    Parameters
    --------------
    member_id: str
        Unique user ID or email.

    role: ProjectMember.Role
        User role in project.

    stages: Optional[List[str]] = None
        Stages that the member has access to (Applicable for MEMBER role).

    org_membership: Optional[OrgMember] = None
        Organization memberhip.
        This is not required when adding/updating a member.
    """

    class Role(str, Enum):
        """Enumerate access levels for Project.

        - ``ADMIN`` - Project Admin
        - ``MANAGER`` - Project Manager
        - ``MEMBER`` - Project Member (Labeler/Reviewer)

        """

        ADMIN = "ADMIN"
        MANAGER = "MANAGER"
        MEMBER = "MEMBER"

    member_id: str
    role: "ProjectMember.Role"
    stages: Optional[List[str]] = None
    org_membership: Optional[OrgMember] = None

    @classmethod
    def from_entity(cls, member: Dict) -> "ProjectMember":
        """Get object from entity."""
        role = ProjectMember.Role(
            "MEMBER" if member["role"] == "LABELER" else member["role"]
        )
        return cls(
            member_id=member["member"]["user"]["userId"],
            role=role,
            stages=(
                [
                    stage["stageName"]
                    for stage in member["stageAccess"]
                    if stage["access"]
                ]
                if role == ProjectMember.Role.MEMBER
                else None
            ),
            org_membership=OrgMember.from_entity(member["member"]),
        )


class MemberRepo(ABC):
    """Abstract interface to define methods for Member."""

    @abstractmethod
    def list_org_members(self, org_id: str, active: bool = True) -> List[Dict]:
        """Get a list of all org members."""

    @abstractmethod
    def list_api_keys(self, org_id: str) -> List[Dict]:
        """Get a list of all API keys."""

    @abstractmethod
    def toggle_org_members_status(
        self, org_id: str, user_ids: List[str], active: bool
    ) -> None:
        """Toggle org members status."""

    @abstractmethod
    def list_org_invites(self, org_id: str) -> List[Dict]:
        """Get a list of all org invites."""

    @abstractmethod
    def invite_org_user(self, org_id: str, invitation: Dict) -> Dict:
        """Invite an user to the organization."""

    @abstractmethod
    def delete_org_invitation(self, org_id: str, invitation: Dict) -> None:
        """Delete an org invitation."""

    @abstractmethod
    def list_project_members(self, org_id: str, project_id: str) -> List[Dict]:
        """Get a list of all project members."""

    @abstractmethod
    def update_project_memberships(
        self, org_id: str, project_id: str, memberships: List[Dict]
    ) -> None:
        """Update project memberships."""

    @abstractmethod
    def remove_project_members(
        self, org_id: str, project_id: str, user_ids: List[str]
    ) -> None:
        """Remove project members."""


class Team(ABC):
    """Abstract interface to Team module."""

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
    def list_invites(self) -> List[OrgInvite]:
        """Get a list of all pending or declined invites.

        .. code:: python

            org = redbrick.get_org(org_id, api_key)
            members = org.team.list_invites()

        Returns
        -------------
        List[OrgInvite]
        """

    @abstractmethod
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

    @abstractmethod
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


class Workforce(ABC):
    """Abstract interface to Workforce module."""

    @abstractmethod
    def get_member(self, member_id: str) -> ProjectMember:
        """Get a project member.

        .. code:: python

            project = redbrick.get_project(org_id, project_id, api_key)
            member = project.workforce.get_member(member_id)

        Parameters
        --------------
        member_id: str
            Unique member userId or email.

        Returns
        -------------
        ProjectMember
        """

    @abstractmethod
    def list_members(self) -> List[ProjectMember]:
        """Get a list of all project members.

        .. code:: python

            project = redbrick.get_project(org_id, project_id, api_key)
            members = project.workforce.list_members()

        Returns
        -------------
        List[ProjectMember]
        """

    @abstractmethod
    def add_members(self, members: List[ProjectMember]) -> List[ProjectMember]:
        """Add project members.

        .. code:: python

            project = redbrick.get_project(org_id, project_id, api_key)
            member = project.workforce.add_members([{"member_id": "...", "role": "...", "stages": ["..."]}, ...])

        Parameters
        --------------
        members: List[ProjectMember]
            List of members to add.

        Returns
        -------------
        List[ProjectMember]
            List of added project members.
        """

    @abstractmethod
    def update_members(self, members: List[ProjectMember]) -> List[ProjectMember]:
        """Update project members.

        .. code:: python

            project = redbrick.get_project(org_id, project_id, api_key)
            member = project.workforce.update_members([{"member_id": "...", "role": "...", "stages": ["..."]}, ...])

        Parameters
        --------------
        members: List[ProjectMember]
            List of members to update.

        Returns
        -------------
        List[ProjectMember]
            List of updated project members.
        """

    @abstractmethod
    def remove_members(self, member_ids: List[str]) -> None:
        """Remove project members.

        .. code:: python

            project = redbrick.get_project(org_id, project_id, api_key)
            member = project.workforce.remove_members([...])

        Parameters
        --------------
        member_ids: List[str]
            List of member ids (user_id/email) to remove from the project.
        """
