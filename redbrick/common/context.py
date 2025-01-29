"""Container for low-level methods to communicate with API."""

from typing import Optional

from redbrick.config import config


class RBContext:
    """Basic context for accessing low level functionality."""

    def __init__(self, api_key: str, url: str) -> None:
        """Construct RedBrick client singleton."""
        # pylint: disable=import-outside-toplevel
        from .client import RBClient
        from .export import ExportControllerInterface
        from .upload import UploadControllerInterface
        from .labeling import LabelingControllerInterface
        from .settings import SettingsControllerInterface
        from .project import ProjectRepoInterface
        from .workspace import WorkspaceRepoInterface
        from .workforce import WorkforceControllerInterface
        from .storage_method import StorageMethodRepoInterface

        self.config = config
        self.client = RBClient(api_key=api_key, url=url)

        self.export: ExportControllerInterface
        self.upload: UploadControllerInterface
        self.labeling: LabelingControllerInterface
        self.settings: SettingsControllerInterface
        self.project: ProjectRepoInterface
        self.workspace: WorkspaceRepoInterface
        self.workforce: WorkforceControllerInterface
        self.storage_method: StorageMethodRepoInterface

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
