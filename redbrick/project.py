"""Main object for RedBrick SDK."""
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dateutil import parser  # type: ignore

import tenacity
from tenacity.retry import retry_if_not_exception_type
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_exponential
from redbrick.common.constants import PEERLESS_ERRORS

from redbrick.common.context import RBContext
from redbrick.common.enums import LabelType, StorageMethod
from redbrick.utils.logging import logger


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
        self._created_at: datetime

        self.consensus_enabled: bool = False
        self._label_storage: Optional[Tuple[str, str]] = None

        # check if project exists on backend to validate
        self._get_project()

        self.upload = Upload(context, org_id, project_id, self.project_type)

        self.output_stage_name: str = "Output"
        for stage in self._stages:
            if stage["brickName"] == "labelset-output":
                self.output_stage_name = stage["stageName"]

        self.labeling = Labeling(context, org_id, project_id)
        self.review = Labeling(context, org_id, project_id, review=True)
        self.export = Export(
            context,
            org_id,
            project_id,
            self.project_type,
            self.output_stage_name,
            self.consensus_enabled,
            self.label_stages,
            self.review_stages,
            self.taxonomy_name,
        )

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

    @property
    def label_storage(self) -> Tuple[str, str]:
        """
        Read only label_storage property.

        Retrieves the label storage id and path.
        """
        if not self._label_storage:
            self._label_storage = self.context.project.get_label_storage(
                self.org_id, self.project_id
            )
        return self._label_storage

    @property
    def label_stages(self) -> List[Dict]:
        """Get list of label stages."""
        return [
            stage for stage in self._stages if stage["brickName"] == "manual-labeling"
        ]

    @property
    def review_stages(self) -> List[Dict]:
        """Get list of review stages."""
        return [
            stage for stage in self._stages if stage["brickName"] == "expert-review"
        ]

    @property
    def members(self) -> List[Dict]:
        """Get list of project members."""
        members = self.context.project.get_members(self.org_id, self.project_id)
        project_members = []
        for member in members:
            member_obj = member.get("member", {})
            user_obj = member_obj.get("user", {})
            project_members.append(
                {
                    "userId": user_obj.get("userId"),
                    "email": user_obj.get("email"),
                    "givenName": user_obj.get("givenName"),
                    "familyName": user_obj.get("familyName"),
                    "role": member_obj.get("role"),
                    "tags": member_obj.get("tags"),
                    "stageAccess": member.get("stageAccess"),
                }
            )
        return project_members

    def __wait_for_project_to_finish_creating(self) -> Dict:
        project = {}
        try:
            for attempt in tenacity.Retrying(
                reraise=True,
                stop=stop_after_attempt(10),
                wait=wait_exponential(multiplier=1, min=1, max=10),
                retry=retry_if_not_exception_type(PEERLESS_ERRORS),
            ):
                with attempt:
                    project = self.context.project.get_project(
                        self.org_id, self.project_id
                    )
                    if project["status"] == "CREATING":
                        if attempt.retry_state.attempt_number == 1:
                            logger.info("Project is still creating...")
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
        self._created_at = parser.parse(project["createdAt"])
        self.consensus_enabled = project["consensusSettings"]["enabled"]

    def __str__(self) -> str:
        """Get string representation of RBProject object."""
        return f"RedBrick Project - {self.name} - id:( {self.project_id} )"

    def __repr__(self) -> str:
        """Representation of object."""
        return str(self)

    def set_label_storage(self, storage_id: str, path: str) -> Tuple[str, str]:
        """
        Set label storage method for a project.

        By default, all annotations get stored in RedBrick AI's storage
        i.e. redbrick.StorageMethod.REDBRICK.
        Set a custom external storage, within which RedBrick AI will write all annotations.

        Parameters
        ------------
        storage_id: str
            The unique ID of your RedBrick AI storage method integration.
            Found on the storage method tab on the left sidebar.

        path: str
            A prefix path within which the annotations will be written.

        Returns
        --------------
        Tuple[str, str]
            Returns [storage_id, path]

        Warnings
        ------------
        - You can only set external storage for DICOM_SEGMENTATION projects.
        - You only need to run this command once per project.

        """
        path = (
            f"{self.org_id}/{self.project_id}"
            if storage_id == StorageMethod.REDBRICK
            else path.rstrip("/")
        )
        self.context.project.set_label_storage(
            self.org_id, self.project_id, storage_id, path
        )
        self._label_storage = (storage_id, path)
        return self.label_storage
