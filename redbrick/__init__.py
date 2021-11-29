"""
RedBrick SDK is a Python package for the RedBrick AI platform.

Visit https://docs.redbrickai.com/python-sdk/sdk-overview for an
overview of how to use the SDK and to view code examples.

To use the RedBrick SDK you need to create an API key. Please
see this documentation for accomplishing that.
https://docs.redbrickai.com/python-sdk/sdk-overview#generate-an-api-key
"""

from redbrick.common.context import RBContext
from redbrick.common.enums import LabelType, StorageMethod
from redbrick.project import RBProject
from redbrick.organization import RBOrganization
from redbrick.utils import version_check  # pylint: disable=cyclic-import
from redbrick.repo import (
    ExportRepo,
    LabelingRepo,
    LearningRepo,
    Learning2Repo,
    UploadRepo,
    ProjectRepo,
)

version_check.version_check()


def _populate_context(context: RBContext) -> RBContext:
    context.export = ExportRepo(context.client)
    context.labeling = LabelingRepo(context.client)
    context.learning = LearningRepo(context.client)
    context.learning2 = Learning2Repo(context.client)
    context.upload = UploadRepo(context.client)
    context.project = ProjectRepo(context.client)
    return context


def get_org(api_key: str, url: str, org_id: str) -> RBOrganization:
    """
    Create a redbrick organization object.

    Organization object allows you to interact with your organization
    and perform high level actions like creating a project.

    Parameters
    ---------------
    api_key: str
        Your secret api_key, can be created from the RedBrick AI platform.

    url: str
        Should default to https://api.redbrickai.com

    org_id: str
        Your organizations unique id https://app.redbrickai.com/<org_id>/.
    """
    context = _populate_context(RBContext(api_key, url))
    return RBOrganization(context, org_id)


def get_project(api_key: str, url: str, org_id: str, project_id: str) -> RBProject:
    """
    Create a RedBrick project object.

    Project objects allow you to interact with your RedBrick Ai projects,
    and perform actions like importing data, exporting data etc.

    Parameters
    ---------------
    api_key: str
        Your secret api_key, can be created from the RedBrick AI platform.

    url: str
        Should default to https://api.redbrickai.com

    org_id: str
        Your organizations unique id https://app.redbrickai.com/<org_id>/

    project_id: str
        Your projects unique id https://app.redbrickai.com/<org_id>/<project_id>/
    """
    context = _populate_context(RBContext(api_key, url))
    return RBProject(context, org_id, project_id)
