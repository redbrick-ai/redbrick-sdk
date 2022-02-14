"""Container for low-level methods to communicate with API."""


class RBContext:
    """Basic context for accessing low level functionality."""

    def __init__(self, api_key: str, url: str) -> None:
        """Construct RedBrick client singleton."""
        # pylint: disable=import-outside-toplevel
        from .client import RBClient
        from .export import ExportControllerInterface
        from .upload import UploadControllerInterface
        from .labeling import LabelingControllerInterface
        from .learning import LearningControllerInterface, LearningController2Interface
        from .project import ProjectRepoInterface

        self.client = RBClient(api_key=api_key, url=url)

        self.export: ExportControllerInterface
        self.upload: UploadControllerInterface
        self.labeling: LabelingControllerInterface
        self.learning: LearningControllerInterface
        self.learning2: LearningController2Interface
        self.project: ProjectRepoInterface

    def __str__(self) -> str:
        """Get string representation."""
        return repr(self) + (
            "***" + self.client.api_key[-3:] if self.client.api_key else ""
        )
