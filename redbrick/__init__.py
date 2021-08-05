"""
RedBrick SDK to enable powerful use cases.

- To begin use: redbrick.get_project(api_key, org_id, project_id)
- Start at https://app.redbrickai.com to create a project.
- Learn more at https://docs.redbrickai.com


"""

from redbrick.common.context import RBContext
from redbrick.common.enums import LabelType
from redbrick.project import RBProject
from redbrick.organization import RBOrganization
from redbrick.utils import version_check
from redbrick.repo import (
    ExportRepo,
    LabelingRepo,
    LearningRepo,
    UploadRepo,
    ProjectRepo,
)

version_check.version_check()


def _populate_context(context: RBContext) -> RBContext:
    context.export = ExportRepo(context.client)
    context.labeling = LabelingRepo(context.client)
    context.learning = LearningRepo(context.client)
    context.upload = UploadRepo(context.client)
    context.project = ProjectRepo(context.client)
    return context


def get_org(api_key: str, url: str, org_id: str) -> RBOrganization:
    """Get redbrick organization object."""
    context = _populate_context(RBContext(api_key, url))
    return RBOrganization(context, org_id)


def get_project(api_key: str, url: str, org_id: str, project_id: str) -> RBProject:
    """Get project object."""
    context = _populate_context(RBContext(api_key, url))
    return RBProject(context, org_id, project_id)
