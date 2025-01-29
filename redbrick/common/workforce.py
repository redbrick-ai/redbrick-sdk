"""Abstract interface to workforce."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
from abc import ABC, abstractmethod

from dateutil import parser  # type: ignore

from redbrick.common.enums import OrgMemberRole, ProjectMemberRole


@dataclass
class OrgMember:
    """Organization Member.

    Parameters
    --------------
    user_id: str
        User ID

    email: str
        User email

    given_name: str
        User given name

    family_name: str
        User family name

    role: OrgMemberRole
        User role in organization

    tags: List[str]
        Tags associated with the user

    is_2fa_enabled: bool
        Whether 2FA is enabled for the user

    last_active: datetime
        Last time the user was active
    """

    user_id: str
    email: str
    given_name: str
    family_name: str
    role: OrgMemberRole
    tags: List[str]
    is_2fa_enabled: bool
    last_active: datetime

    @classmethod
    def from_entity(cls, member: Dict) -> "OrgMember":
        return cls(
            user_id=member["user"]["userId"],
            email=member["user"]["email"],
            given_name=member["user"]["givenName"],
            family_name=member["user"]["familyName"],
            role=OrgMemberRole(member["role"]),
            tags=member["tags"],
            is_2fa_enabled=bool(member["user"]["mfaSetup"]),
            last_active=parser.parse(
                member.get(
                    "lastSeen",
                    member["user"].get("lastSeen", member["user"]["updatedAt"]),
                )
            ),
        )


@dataclass
class ProjectMember:
    """Project Member.

    Parameters
    --------------
    member_id: str
        Unique user ID or email

    role: ProjectMemberRole
        User role in project

    stages: Optional[List[str]] = None
        Stages that the member has access to (Applicable for MEMBER role)

    org_member: Optional[OrgMember] = None
        Organization member
        This is not required when adding/updating a member.
    """

    member_id: str
    role: ProjectMemberRole
    stages: Optional[List[str]] = None
    org_member: Optional[OrgMember] = None

    @classmethod
    def from_entity(cls, member: Dict) -> "ProjectMember":
        """Get object from entity."""
        role = ProjectMemberRole(
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
                if role == ProjectMemberRole.MEMBER
                else None
            ),
            org_member=OrgMember.from_entity(member["member"]),
        )


class WorkforceControllerInterface(ABC):
    """Abstract interface to define methods for Member."""

    @abstractmethod
    def list_org_members(self, org_id: str) -> List[Dict]:
        """Get a list of all org members."""

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
