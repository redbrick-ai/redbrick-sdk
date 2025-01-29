"""Abstract interface to project workforce."""

from dataclasses import dataclass
from typing import Dict, List, Optional, TypedDict
from abc import ABC, abstractmethod
from typing_extensions import NotRequired  # type: ignore

from redbrick.common.enums import OrgMemberRole, ProjectMemberRole


@dataclass
class ProjectMember:
    """Project Member.

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

    org_role: OrgMemberRole
        User role in organization

    project_role: ProjectMemberRole
        User role in project

    tags: List[str]
        Tags associated with the user

    stages: Optional[List[str]] = None
        Stages that the member has access to (Applicable for MEMBER role)
    """

    user_id: str
    email: str
    given_name: str
    family_name: str
    org_role: OrgMemberRole
    project_role: ProjectMemberRole
    tags: List[str]
    stages: Optional[List[str]] = None

    @classmethod
    def from_entity(cls, member: Dict) -> "ProjectMember":
        """Get object from entity."""
        role = ProjectMemberRole(
            "MEMBER" if member["role"] == "LABELER" else member["role"]
        )
        return cls(
            user_id=member["member"]["user"]["userId"],
            email=member["member"]["user"]["email"],
            given_name=member["member"]["user"]["givenName"],
            family_name=member["member"]["user"]["familyName"],
            org_role=OrgMemberRole(member["member"]["role"]),
            project_role=role,
            tags=member["member"]["tags"],
            stages=(
                [
                    stage["stageName"]
                    for stage in member["stageAccess"]
                    if stage["access"]
                ]
                if role == ProjectMemberRole.MEMBER
                else None
            ),
        )


@dataclass
class ProjectMemberInput(TypedDict):
    """Project Member Input."""

    #: Member ID (Either unique email or userId)
    member_id: str

    #: Member role
    role: ProjectMemberRole

    #: Stages that the member has access to (Applicable for MEMBER role)
    stages: NotRequired[List[str]]


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
