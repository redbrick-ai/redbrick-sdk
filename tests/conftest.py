"""Fixtures for all tests"""
import pytest

from redbrick import RBContext
from redbrick.common.client import RBClient
from redbrick.export import Export
from redbrick.repo import (
    ExportRepo,
    LabelingRepo,
    UploadRepo,
    SettingsRepo,
    ProjectRepo,
    WorkspaceRepo,
)


@pytest.fixture(scope="function")
def rb_context() -> RBContext:
    """Get a new mock RBContext for each test"""
    context = RBContext(
        api_key="mock_api_key_000000000000000000000000000000", url="mock_url"
    )
    return context


@pytest.fixture(scope="function")
def rb_client(
    rb_context: RBContext,  # pylint: disable=redefined-outer-name
) -> RBClient:
    """Get a new mock RBClient for each test"""
    return rb_context.client


@pytest.fixture(scope="function")
def mock_export_repo(
    rb_client: RBClient,  # pylint: disable=redefined-outer-name
) -> ExportRepo:
    """Get a new mock ExportRepo object for each test"""
    export_repo = ExportRepo(rb_client)
    return export_repo


def _mock_populate_context(
    context: RBContext,
    export_repo=None,
    labeling_repo=None,
    upload_repo=None,
    settings_repo=None,
    project_repo=None,
    workspace_repo=None,
) -> RBContext:
    context.export = export_repo or ExportRepo(context.client)
    context.labeling = labeling_repo or LabelingRepo(context.client)
    context.upload = upload_repo or UploadRepo(context.client)
    context.settings = settings_repo or SettingsRepo(context.client)
    context.project = project_repo or ProjectRepo(context.client)
    context.workspace = workspace_repo or WorkspaceRepo(context.client)
    return context


@pytest.fixture(scope="function")
def mock_export(
    mock_export_repo: ExportRepo,  # pylint: disable=redefined-outer-name
) -> Export:
    """Get a new mock Export object for each test"""
    context = RBContext(
        api_key="mock_api_key_000000000000000000000000000000", url="mock_url"
    )
    context = _mock_populate_context(context, export_repo=mock_export_repo)
    export = Export(
        context=context,
        org_id="mock_org_id",
        project_id="mock_project_id",
        output_stage_name="END",
        consensus_enabled=True,
        label_stages=[{"stageName": "Label"}],
        review_stages=[{"stageName": "Review_1"}, {"stageName": "Review_2"}],
        taxonomy_name="mock_taxonomy_name",
    )
    return export