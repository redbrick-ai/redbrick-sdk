"""Fixtures for all tests"""

import pytest

from redbrick import RBContext, _populate_context
from redbrick.common.client import RBClient
from redbrick.export import Export
from redbrick.repo import ExportRepo
from redbrick.stage import LabelStage, ReviewStage


@pytest.fixture(scope="function")
def rb_context() -> RBContext:
    """Get a new mock RBContext for each test"""
    context = RBContext(
        api_key="mock_api_key_000000000000000000000000000000", url="mock_url"
    )
    return context


@pytest.fixture(scope="function")
def rb_context_full() -> RBContext:
    """Get a new mock RBContext for each test"""
    context = RBContext(
        api_key="mock_api_key_000000000000000000000000000000", url="mock_url"
    )
    context = _populate_context(context)
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


@pytest.fixture(scope="function")
def mock_export(
    mock_export_repo: ExportRepo,  # pylint: disable=redefined-outer-name
) -> Export:
    """Get a new mock Export object for each test"""
    context = RBContext(
        api_key="mock_api_key_000000000000000000000000000000", url="mock_url"
    )
    context = _populate_context(context)
    context.export = mock_export_repo
    export = Export(
        context=context,
        org_id="mock_org_id",
        project_id="mock_project_id",
        output_stage_name="END",
        consensus_enabled=True,
        label_stages=[LabelStage(stage_name="Label")],
        review_stages=[ReviewStage("Review_1"), ReviewStage("Review_2")],
        taxonomy_name="mock_taxonomy_name",
    )
    return export
