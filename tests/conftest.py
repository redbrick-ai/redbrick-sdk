"""Fixtures for all tests"""

from datetime import datetime
from unittest.mock import Mock
import pytest

from redbrick.common.entities import RBContext
from redbrick.common.context import RBContextImpl
from redbrick.export import ExportImpl
from redbrick.project import RBProjectImpl
from redbrick.repo import ExportRepoImpl


@pytest.fixture(scope="function", name="rb_context")
def mock_rb_context() -> RBContext:
    """Get a new mock RBContext for each test"""
    return RBContextImpl(
        api_key="mock_api_key_000000000000000000000000000000",
        url="mock_url",
    )


@pytest.fixture(scope="function", name="export_repo")
def export_repo(rb_context: RBContext) -> ExportRepoImpl:
    """Get a new mock ExportRepoImpl object for each test"""
    export_repo = ExportRepoImpl(rb_context.client)
    return export_repo


@pytest.fixture(scope="function", name="export")
def export(rb_context: RBContext, export_repo: ExportRepoImpl) -> ExportImpl:
    """Get a new mock Export object for each test"""
    org_id = "mock_org_id"
    project_id = "mock_project_id"

    mock_project_resp = {
        "orgId": org_id,
        "projectId": project_id,
        "name": "mock_project",
        "tdType": "mock_tdType",
        "taxonomy": {"name": "mock_taxonomy"},
        "workspace": {"workspaceId": "mock_workspace_id"},
        "projectUrl": "mock_project_url",
        "createdAt": datetime.now().isoformat(),
        "consensusSettings": {"enabled": True},
        "status": "CREATION_SUCCESS",
    }
    mock_taxonomy_resp = {
        "orgId": org_id,
        "taxId": project_id,
        "name": "mock_taxonomy",
        "studyClassify": [],
        "seriesClassify": [],
        "instanceClassify": [],
        "objectTypes": [],
        "createdAt": datetime.now().isoformat(),
    }

    mock_stages_resp = [
        {
            "stageName": "Label",
            "brickName": "manual-labeling",
            "routing": {"nextStageName": "Review_1"},
        },
        {
            "stageName": "Review_1",
            "brickName": "expert-review",
            "routing": {"passed": "Review_2", "failed": "Label"},
        },
        {
            "stageName": "Review_2",
            "brickName": "expert-review",
            "routing": {"passed": "END", "failed": "Label"},
        },
        {"stageName": "END", "brickName": "labelset-output", "routing": {}},
    ]

    rb_context.project.get_project = Mock(return_value=mock_project_resp)
    rb_context.project.get_taxonomy = Mock(return_value=mock_taxonomy_resp)
    rb_context.project.get_stages = Mock(return_value=mock_stages_resp)
    rb_context.export = export_repo

    return ExportImpl(RBProjectImpl(rb_context, org_id, project_id))
