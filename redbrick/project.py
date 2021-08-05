"""Main object for RedBrick SDK."""

import time
from typing import Dict, List
from redbrick.common.context import RBContext

from redbrick.export import Export
from redbrick.upload import Upload
from redbrick.learning import Learning
from redbrick.labeling import Labeling
from redbrick.utils.logging import print_info


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
    def name(self) -> str:
        """Read only name property."""
        return self._project_name

    @property
    def learning(self) -> Learning:
        """Read only, get learning module."""
        for stage in self._stages:
            if stage["brickName"] == "active-learning":
                return Learning(
                    self.context, self.org_id, self.project_id, stage["stageName"]
                )

        raise Exception("No active learning stage in this project")

    def __wait_for_project_to_finish_creating(self) -> Dict:
        project = self.context.project.get_project(self.org_id, self.project_id)
        if project["status"] == "CREATING":
            print_info("Project is still creating...", end="")
            for ii in range(8):
                print_info(".", end="")
                time.sleep(2 ^ ii)
                project = self.context.project.get_project(self.org_id, self.project_id)
                if project["status"] != "CREATING":
                    break

        if project["status"] == "REMOVING":
            raise Exception("Project has been deleted")
        if project["status"] == "CREATION_FAILURE":
            raise Exception("Project failed to be created")
        if project["status"] == "CREATION_SUCCESS":
            return project
        raise Exception("Unknown problem occurred")

    def _get_project(self) -> None:
        """Get project to confirm it exists."""
        project = self.__wait_for_project_to_finish_creating()

        self._project_name = project["name"]
        self._stages = self.context.project.get_stages(self.org_id, self.project_id)

    def __str__(self) -> str:
        """Get string representation of RBProject object."""
        return f"RedBrick Project - {self.name} - id:( {self.project_id} )"

    def __repr__(self) -> str:
        """Representation of object."""
        return str(self)
