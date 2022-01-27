"""
Configure pytest.

Reusable fixtures.
"""
import os

import pytest

from redbrick import _populate_context
from redbrick.common.context import RBContext
from redbrick.organization import RBOrganization
from redbrick.project import RBProject


@pytest.fixture(name="api_key")
def fixture_api_key() -> str:
    """Get api_key."""
    return os.environ.get("REDBRICK_SDK_API_KEY", "")


@pytest.fixture(name="url")
def fixture_url() -> str:
    """Get url."""
    return os.environ.get("REDBRICK_SDK_URL", "")


@pytest.fixture(name="org_id")
def fixture_org_id() -> str:
    """Get org_id."""
    return os.environ.get("REDBRICK_SDK_ORG_ID", "")


@pytest.fixture(name="project_id")
def fixture_project_id() -> str:
    """Get project_id."""
    return os.environ.get("REDBRICK_SDK_PROJECT_ID", "")


@pytest.fixture(name="context")
def fixture_context(api_key: str, url: str) -> RBContext:
    """Get RBContext."""
    return _populate_context(RBContext(api_key=api_key, url=url))


@pytest.fixture(name="org")
def fixture_org(context: RBContext, org_id: str) -> RBOrganization:
    """Get RBOrganization."""
    return RBOrganization(context, org_id)


@pytest.fixture(name="project")
def fixture_project(context: RBContext, org_id: str, project_id: str) -> RBProject:
    """Get RBProject."""
    return RBProject(context, org_id, project_id)
