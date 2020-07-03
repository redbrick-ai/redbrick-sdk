"""Public interface to remote_label."""


class RemoteLabel:
    """An interface to RemoteLabel brick."""

    def __init__(self, org_id: str, project_id: str, stage_name: str) -> None:
        """Construct RemoteLabel instance."""
        self.org_id = org_id
        self.project_id = project_id
        self.stage_name = stage_name
