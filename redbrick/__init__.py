""""""

import os
import sys
import asyncio
from typing import Optional
from configparser import ConfigParser


import nest_asyncio  # type: ignore

from redbrick.common.context import RBContext
from redbrick.common.enums import (
    StorageMethod,
    ImportTypes,
    TaskEventTypes,
    TaskFilters,
)
from redbrick.common.constants import DEFAULT_URL
from redbrick.organization import RBOrganization
from redbrick.workspace import RBWorkspace
from redbrick.project import RBProject
from redbrick.stage import Stage, LabelStage, ReviewStage, ModelStage

from redbrick.utils.logging import logger
from redbrick.utils.common_utils import config_migration, config_path

from redbrick.types import task as TaskTypes, taxonomy as TaxonomyTypes

from .config import config
from .version_check import version_check

__version__ = "2.18.1"

# windows event loop close bug https://github.com/encode/httpx/issues/914#issuecomment-622586610
try:
    if (
        sys.version_info[0] == 3
        and sys.version_info[1] >= 8
        and sys.platform.startswith("win")
    ):
        asyncio.set_event_loop_policy(  # type: ignore
            asyncio.WindowsSelectorEventLoopPolicy()  # type: ignore
        )
except Exception:  # pylint: disable=broad-except
    pass

# if there is a running event loop, apply nest_asyncio
try:
    if asyncio._get_running_loop() is None:  # pylint: disable=protected-access
        raise RuntimeError
    nest_asyncio.apply()
    logger.warning(
        "Applying nest-asyncio to a running event loop, this likely means you're in a jupyter"
        + " notebook and you can safely ignore this."
    )
except (RuntimeError, AttributeError):
    pass

try:
    config_migration()
except Exception:  # pylint: disable=broad-except
    pass


def version() -> str:
    """Check for latest version and return the current one."""
    version_check(__version__, config.check_version)
    return f"v{__version__}"


def _populate_context(context: RBContext) -> RBContext:
    # pylint: disable=import-outside-toplevel
    from redbrick.repo import (
        ExportRepo,
        LabelingRepo,
        UploadRepo,
        SettingsRepo,
        ProjectRepo,
        WorkspaceRepo,
    )

    if context.config.debug:
        logger.debug(f"Using: redbrick-sdk=={__version__}")

    context.export = ExportRepo(context.client)
    context.labeling = LabelingRepo(context.client)
    context.upload = UploadRepo(context.client)
    context.settings = SettingsRepo(context.client)
    context.project = ProjectRepo(context.client)
    context.workspace = WorkspaceRepo(context.client)
    return context


def get_org(org_id: str, api_key: str, url: str = DEFAULT_URL) -> RBOrganization:
    """
    Get an existing redbrick organization object.

    Organization object allows you to interact with your organization
    and perform high level actions like creating a project.

    >>> org = redbrick.get_org(org_id, api_key)

    Parameters
    ---------------
    org_id: str
        Your organizations unique id https://app.redbrickai.com/<org_id>/.

    api_key: str
        Your secret api_key, can be created from the RedBrick AI platform.

    url: str = DEFAULT_URL
        Should default to https://api.redbrickai.com
    """
    context = _populate_context(RBContext(api_key=api_key, url=url))
    return RBOrganization(context, org_id)


def get_workspace(
    org_id: str, workspace_id: str, api_key: str, url: str = DEFAULT_URL
) -> RBWorkspace:
    """
    Get an existing RedBrick workspace object.

    Workspace objects allow you to interact with your RedBrick AI workspaces,
    and perform actions like importing data, exporting data etc.

    >>> workspace = redbrick.get_workspace(org_id, workspace_id, api_key)

    Parameters
    ---------------
    org_id: str
        Your organizations unique id https://app.redbrickai.com/<org_id>/

    workspace_id: str
        Your workspaces unique id.

    api_key: str
        Your secret api_key, can be created from the RedBrick AI platform.

    url: str = DEFAULT_URL
        Should default to https://api.redbrickai.com
    """
    context = _populate_context(RBContext(api_key=api_key, url=url))
    return RBWorkspace(context, org_id, workspace_id)


def get_project(
    org_id: str, project_id: str, api_key: str, url: str = DEFAULT_URL
) -> RBProject:
    """
    Get an existing RedBrick project object.

    Project objects allow you to interact with your RedBrick Ai projects,
    and perform actions like importing data, exporting data etc.

    >>> project = redbrick.get_project(org_id, project_id, api_key)

    Parameters
    ---------------
    org_id: str
        Your organizations unique id https://app.redbrickai.com/<org_id>/

    project_id: str
        Your projects unique id https://app.redbrickai.com/<org_id>/<project_id>/

    api_key: str
        Your secret api_key, can be created from the RedBrick AI platform.

    url: str = DEFAULT_URL
        Should default to https://api.redbrickai.com
    """
    context = _populate_context(RBContext(api_key=api_key, url=url))
    return RBProject(context, org_id, project_id)


def get_org_from_profile(
    profile_name: Optional[str] = None,
) -> RBOrganization:
    """Get the org from the profile name in credentials file"""
    # pylint: disable=import-outside-toplevel, cyclic-import
    from redbrick.cli.entity import CLICredentials

    creds_file = os.path.join(config_path(), "credentials")
    creds = CLICredentials(creds_file)
    org_creds = creds.get_profile(profile_name or creds.selected_profile)
    api_key, org_id, url = (
        org_creds["key"],
        org_creds["org"],
        org_creds["url"],
    )
    return get_org(org_id, api_key, url)


def get_project_from_profile(
    project_id: Optional[str] = None, profile_name: Optional[str] = None
) -> Optional[RBProject]:
    """Get the RBProject object using the credentials file"""
    # pylint: disable=import-outside-toplevel, cyclic-import
    from redbrick.cli.project import CLIProject
    from redbrick.cli.entity import CLICredentials

    if not project_id:

        cli_project = CLIProject.from_path(required=False)
        if cli_project:
            return cli_project.project
        logger.error(
            f"{get_project_from_profile.__name__}"
            + " called without a project id outside a project directory"
        )
        return None
    creds_file = os.path.join(config_path(), "credentials")
    creds = CLICredentials(creds_file)
    org_creds = creds.get_profile(profile_name or creds.selected_profile)
    api_key, org_id, url = (
        org_creds["key"],
        org_creds["org"],
        org_creds["url"],
    )
    return get_project(org_id, project_id, api_key, url)


__all__ = [
    "__version__",
    "config",
    "version",
    "RBContext",
    "StorageMethod",
    "ImportTypes",
    "TaxonomyTypes",
    "TaskTypes",
    "TaskEventTypes",
    "TaskFilters",
    "Stage",
    "LabelStage",
    "ReviewStage",
    "ModelStage",
    "RBOrganization",
    "RBWorkspace",
    "RBProject",
    "get_org",
    "get_workspace",
    "get_project",
    "get_org_from_profile",
    "get_project_from_profile",
]
