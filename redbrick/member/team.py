"""Public interface to team controller."""

from typing import List

from redbrick.common.context import RBContext
from redbrick.common.member import OrgMember


class Team:
    """Primary interface to organization team."""

    def __init__(self, context: RBContext, org_id: str) -> None:
        """Construct Member object."""
        self.context = context
        self.org_id = org_id

    def list_members(self) -> List[OrgMember]:
        """Get a list of all organization members.

        .. code:: python

            org = redbrick.get_org(org_id, api_key)
            members = org.team.list_members()

        Returns
        -------------
        List[OrgMember]
        """
        members = self.context.member.list_org_members(self.org_id)
        return [OrgMember.from_entity(member) for member in members]
