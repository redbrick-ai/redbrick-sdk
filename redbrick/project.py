"""Main object for RedBrick SDK."""

from typing import Dict, List
from redbrick.common.context import RBContext

from redbrick.export import Export
from redbrick.upload import Upload
from redbrick.learning import Learning
from redbrick.labeling import Labeling


class RBProject:
    """Interact with a RedBrick project."""

    def __init__(self, context: RBContext, org_id: str, project_id: str) -> None:
        """Construct RBProject."""
        self.context = context

        self._org_id = org_id
        self._project_id = project_id
        self._project_name: str
        self._stages: List[Dict]

        # check if project exists on backend to validate
        self._get_project()

        self.export = Export(context, org_id, project_id)

        self.labeling = Labeling(context, org_id, project_id)
        self.review = Labeling(context, org_id, project_id, review=True)
        self.upload = Upload(context, org_id, project_id)

    @property
    def org_id(self) -> str:
        """Read only property."""
        return self._org_id

    @property
    def project_id(self) -> str:
        """Read only property."""
        return self._project_id

    @property
    def learning(self) -> Learning:
        """Read only, get learning module."""
        for stage in self._stages:
            if stage["brickName"] == "active-learning":
                return Learning(
                    self.context, self.org_id, self.project_id, stage["stageName"]
                )

        raise Exception("No active learning stage in this project")

    def _get_project(self) -> None:
        """Get project to confirm it exists."""
        self._project_name = self.context.project.get_project_name(
            self.org_id, self.project_id
        )
        self._stages = self.context.project.get_stages(self.org_id, self.project_id)
