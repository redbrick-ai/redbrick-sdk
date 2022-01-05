"""Main object for RedBrick SDK."""

import json
from typing import Dict, List

import tenacity

from redbrick.common.context import RBContext
from redbrick.common.enums import LabelType
from redbrick.utils.logging import print_info


class RBProject:
    """
    Interact with a RedBrick project.

    Attributes
    -----------
    export: redbrick.export.Export
        Interface for managing exporting data and
        labels from your redbrick ai projects.

    labeling: redbrick.labeling.Labeling
        Interface for programmatically labeling your
        redbrick ai tasks.

    review: redbrick.labeling.Labeling
        Interface for programmatically reviewing your
        redbrick ai tasks.

    upload: redbrick.upload.Upload
        Interface for programmatically managing upload
        of your data and labels.
    """

    def __init__(self, context: RBContext, org_id: str, project_id: str) -> None:
        """Construct RBProject."""
        # pylint: disable=import-outside-toplevel
        from redbrick.upload import Upload
        from redbrick.learning import Learning, Learning2
        from redbrick.labeling import Labeling
        from redbrick.export import Export

        self.context = context

        self._org_id = org_id
        self._project_id = project_id
        self._project_name: str
        self._stages: List[Dict]
        self._td_type: str
        self._taxonomy_name: str
        self._project_url: str

        # check if project exists on backend to validate
        self._get_project()

        self.upload = Upload(context, org_id, project_id, self.project_type)

        self.learning = Learning(self.context, self.org_id, self.project_id)
        self.learning2 = Learning2(self.context, self.org_id, self.project_id)
        for stage in self._stages:
            if stage["brickName"] == "manual-labeling":
                if json.loads(stage["stageConfig"]).get("isPrimaryStage"):
                    self.learning2 = Learning2(
                        self.context, self.org_id, self.project_id, stage["stageName"]
                    )
            elif stage["brickName"] == "active-learning":
                self.learning = Learning(
                    self.context, self.org_id, self.project_id, stage["stageName"]
                )

        self.labeling = Labeling(context, org_id, project_id)
        self.review = Labeling(context, org_id, project_id, review=True)
        self.export = Export(context, org_id, project_id, self.project_type)

    @property
    def org_id(self) -> str:
        """
        Read only property.

        Retrieves the unique Organization UUID that this project belongs to
        """
        return self._org_id

    @property
    def project_id(self) -> str:
        """
        Read only property.

        Retrieves the unique Project ID UUID.
        """
        return self._project_id

    @property
    def name(self) -> str:
        """
        Read only name property.

        Retrieves the project name.
        """
        return self._project_name

    @property
    def url(self) -> str:
        """
        Read only property.

        Retrieves the project URL.
        """
        return self._project_url

    @property
    def taxonomy_name(self) -> str:
        """
        Read only taxonomy_name property.

        Retrieves the taxonomy name.
        """
        return self._taxonomy_name

    @property
    def project_type(self) -> LabelType:
        """
        Read only project_type property.

        Retrieves the type of the project.
        """
        return LabelType(self._td_type)

    def __wait_for_project_to_finish_creating(self) -> Dict:
        try:
            for attempt in tenacity.Retrying(
                stop=tenacity.stop_after_attempt(10),
                wait=tenacity.wait_exponential(multiplier=1, min=1, max=10),
                retry=tenacity.retry_if_not_exception_type(
                    (KeyboardInterrupt, PermissionError, ValueError)
                ),
            ):
                with attempt:
                    project = self.context.project.get_project(
                        self.org_id, self.project_id
                    )
                    if project["status"] == "CREATING":
                        if attempt.retry_state.attempt_number == 1:
                            print_info("Project is still creating...")
                        raise Exception("Unknown problem occurred")
        except tenacity.RetryError as error:
            raise Exception("Unknown problem occurred") from error

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
        self._td_type = project["tdType"]
        self._taxonomy_name = project["taxonomy"]["name"]
        self._stages = self.context.project.get_stages(self.org_id, self.project_id)
        self._project_url = project["projectUrl"]

    def __str__(self) -> str:
        """Get string representation of RBProject object."""
        return f"RedBrick Project - {self.name} - id:( {self.project_id} )"

    def __repr__(self) -> str:
        """Representation of object."""
        return str(self)
