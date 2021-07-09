"""
RedBrick SDK to enable powerful use cases.

- To begin use: redbrick.get_project(api_key, org_id, project_id)
- Start at https://app.redbrickai.com to create a project.
- Learn more at https://docs.redbrickai.com


"""

from redbrick.common.context import RBContext
from redbrick.project import RBProject

from redbrick.repo import (
    ExportRepo,
    LabelingRepo,
    LearningRepo,
    UploadRepo,
    ProjectRepo,
)


def get_project(api_key: str, url: str, org_id: str, project_id: str) -> RBProject:
    """Get project object."""
    context = RBContext(api_key, url)
    context.export = ExportRepo(context.client)
    context.labeling = LabelingRepo(context.client)
    context.learning = LearningRepo(context.client)
    context.upload = UploadRepo(context.client)
    context.project = ProjectRepo(context.client)

    return RBProject(context, org_id, project_id)
