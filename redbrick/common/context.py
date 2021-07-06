from .client import RBClient
from .export import ExportControllerInterface
from .upload import UploadControllerInterface
from .labeling import LabelingControllerInterface
from .learning import LearningControllerInterface
from .project import ProjectRepoInterface


class RBContext:
    """Basic context for accessing low level functionality."""

    def __init__(self, api_key: str, url: str) -> None:
        """Construct RedBrick client singleton."""
        self.client = RBClient(api_key, url)

        self.export: ExportControllerInterface
        self.upload: UploadControllerInterface
        self.labeling: LabelingControllerInterface
        self.learning: LearningControllerInterface
        self.project: ProjectRepoInterface

    def __str__(self) -> str:
        """Get string representation."""
        return repr(self) + "***" + self.client.api_key[-4:-1]
