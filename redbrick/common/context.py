"""Container for low-level methods to communicate with API."""

from abc import ABC, abstractmethod
from typing import Optional

from redbrick.common.client import RBClient, RBClientImpl
from redbrick.common.export import ExportRepo
from redbrick.common.labeling import LabelingRepo
from redbrick.common.member import MemberRepo
from redbrick.common.project import ProjectRepo
from redbrick.common.settings import SettingsRepo
from redbrick.common.upload import UploadRepo
from redbrick.common.workspace import WorkspaceRepo
from redbrick.common.storage import StorageRepo
from redbrick.common.dataset import DatasetRepo
from redbrick.config import config
from redbrick.utils.logging import logger


class RBContext(ABC):
    """Basic context for accessing low level functionality."""

    client: RBClient

    export: ExportRepo
    upload: UploadRepo
    labeling: LabelingRepo
    settings: SettingsRepo
    project: ProjectRepo
    workspace: WorkspaceRepo
    member: MemberRepo
    storage: StorageRepo
    dataset: DatasetRepo

    @property
    @abstractmethod
    def key_id(self) -> str:
        """Get key id."""


class RBContextImpl(RBContext):
    """Basic context for accessing low level functionality."""

    def __init__(self, api_key: str, url: str) -> None:
        """Construct RedBrick client singleton."""
        # pylint: disable=import-outside-toplevel, cyclic-import
        from redbrick.repo import (
            ExportRepoImpl,
            LabelingRepoImpl,
            UploadRepoImpl,
            SettingsRepoImpl,
            ProjectRepoImpl,
            WorkspaceRepoImpl,
            MemberRepoImpl,
            StorageRepoImpl,
            DatasetRepoImpl,
        )

        if config.debug:
            logger.debug(f"Using: redbrick-sdk=={config.version}")

        self.client = RBClientImpl(api_key=api_key, url=url)

        self.export = ExportRepoImpl(self.client)
        self.labeling = LabelingRepoImpl(self.client)
        self.upload = UploadRepoImpl(self.client)
        self.settings = SettingsRepoImpl(self.client)
        self.project = ProjectRepoImpl(self.client)
        self.workspace = WorkspaceRepoImpl(self.client)
        self.member = MemberRepoImpl(self.client)
        self.storage = StorageRepoImpl(self.client)
        self.dataset = DatasetRepoImpl(self.client)

        self._key_id: Optional[str] = None

    def __str__(self) -> str:
        """Get string representation."""
        return repr(self) + (
            "***" + self.client.api_key[-3:] if self.client.api_key else ""
        )

    @property
    def key_id(self) -> str:
        """Get key id."""
        if not self._key_id:
            key_id: str = self.project.get_current_user()["userId"]
            self._key_id = key_id
        return self._key_id
