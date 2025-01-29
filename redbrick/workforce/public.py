"""Public interface to workforce module."""

from typing import Dict, List
from redbrick.common.context import RBContext
from redbrick.common.enums import ProjectMemberRole
from redbrick.common.member import ProjectMember


class Workforce:
    """Primary interface to project workforce."""

    def __init__(self, context: RBContext, org_id: str, project_id: str) -> None:
        """Construct Member object."""
        self.context = context
        self.org_id = org_id
        self.project_id = project_id

    def _get_filtered_members(
        self, member_id: str, members: List[ProjectMember]
    ) -> List[ProjectMember]:
        return [
            member
            for member in members
            if member_id == member.member_id
            or (member.org_member and member_id == member.org_member.email)
        ]

    def _get_unique_member(
        self, member_id: str, members: List[ProjectMember]
    ) -> ProjectMember:
        filtered_members = self._get_filtered_members(member_id, members)

        if not filtered_members:
            raise ValueError(
                f"Member {member_id} not found in project {self.project_id}"
            )

        if len(filtered_members) > 1:
            raise ValueError(
                f"Multiple members found with ID: {member_id}. Please use unique userId."
            )

        return filtered_members[0]

    def get_member(self, member_id: str) -> ProjectMember:
        """Get a project member.

        .. code:: python

            project = redbrick.get_project(org_id, project_id, api_key)
            member = project.get_member(member_id)

        Parameters
        --------------
        member_id: str
            Unique member userId or email.

        Returns
        -------------
        ProjectMember
        """
        members = self.list_members()
        return self._get_unique_member(member_id, members)

    def list_members(self) -> List[ProjectMember]:
        """Get a list of all project members.

        .. code:: python

            project = redbrick.get_project(org_id, project_id, api_key)
            members = project.list_members()

        Returns
        -------------
        List[ProjectMember]
        """
        members = self.context.member.list_project_members(self.org_id, self.project_id)
        return [ProjectMember.from_entity(member) for member in members]

    def add_members(self, members: List[ProjectMember]) -> List[ProjectMember]:
        """Add project members.

        .. code:: python

            project = redbrick.get_project(org_id, project_id, api_key)
            member = project.add_members([{"member_id": "...", "role": "...", "stages": ["..."]}, ...])

        Parameters
        --------------
        members: List[ProjectMember]
            List of members to add.

        Returns
        -------------
        List[ProjectMember]
            List of added project members.
        """
        member_ids = {member.member_id for member in members}
        if len(member_ids) != len(members):
            raise ValueError("Duplicate member IDs found in member list")

        prev_members = self.list_members()
        for member in members:
            filtered_members = self._get_filtered_members(
                member.member_id, prev_members
            )
            if filtered_members:
                raise ValueError(
                    f"Member {member.member_id} already exists in project {self.project_id}"
                )

        return self.update_members(members)

    def update_members(self, members: List[ProjectMember]) -> List[ProjectMember]:
        """Update project members.

        .. code:: python

            project = redbrick.get_project(org_id, project_id, api_key)
            member = project.update_members([{"member_id": "...", "role": "...", "stages": ["..."]}, ...])

        Parameters
        --------------
        members: List[ProjectMember]
            List of members to update.

        Returns
        -------------
        List[ProjectMember]
            List of updated project members.
        """
        member_ids = {member.member_id for member in members}
        if len(member_ids) != len(members):
            raise ValueError("Duplicate member IDs found in member list")

        org_members = self.context.member.list_org_members(self.org_id)
        org_user_map: Dict[str, str] = {}
        for org_member in org_members:
            org_user_map[org_member["user"]["userId"]] = org_member["user"]["userId"]
            org_user_map[org_member["user"]["email"]] = org_member["user"]["userId"]

        memberships: List[Dict] = []
        user_ids = set()
        for member in members:
            if member.member_id not in org_user_map:
                raise ValueError(f"Member {member.member_id} is not present in the org")
            if org_user_map[member.member_id] in user_ids:
                raise ValueError(f"Duplicate member object for {member.member_id}")

            user_id = org_user_map[member.member_id]
            user_ids.add(user_id)

            if member.role == ProjectMemberRole.MEMBER:
                memberships.append(
                    {
                        "userId": user_id,
                        "role": "LABELER",
                        "stageAccess": (
                            [
                                {"stageName": stage, "access": True}
                                for stage in (member.stages or [])
                            ]
                        ),
                    }
                )
            else:
                memberships.append(
                    {
                        "userId": user_id,
                        "role": member.role.value,
                        "stageAccess": [],
                    }
                )

        self.context.member.update_project_memberships(
            self.org_id, self.project_id, memberships
        )

        new_members = self.list_members()
        return [
            self._get_unique_member(member.member_id, new_members) for member in members
        ]

    def remove_members(self, member_ids: List[str]) -> None:
        """Remove project members.

        .. code:: python

            project = redbrick.get_project(org_id, project_id, api_key)
            member = project.remove_members([...])

        Parameters
        --------------
        member_ids: List[str]
            List of member ids (user_id/email) to remove from the project.
        """
        prev_members = self.list_members()
        user_ids: List[str] = []
        for member_id in member_ids:
            member = self._get_unique_member(member_id, prev_members)
            user_ids.append(member.member_id)

        self.context.member.remove_project_members(
            self.org_id, self.project_id, user_ids
        )
