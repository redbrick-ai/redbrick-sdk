"""Public interface to remote_label."""


class RemoteLabel:
    """An interface to RemoteLabel brick."""

    def __init__(self, org_id: str, project_id: str, stage_name: str) -> None:
        """Construct RemoteLabel instance."""
        self.org_id = org_id
        self.project_id = project_id
        self.stage_name = stage_name

    def cache_tasks(self):
        """Get the remote labeling task(s) and cache the data."""
        pass

    def label(self):
        """Read labels from local folder, and submit the labels."""
        pass

    def __get_tasks(self):
        """Get the labeling tasks from API."""
        pass

    def __upload_labels(self):
        """Upload the prelabels using API."""
        pass
