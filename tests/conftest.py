"""Fixtures for all tests"""
import pytest

from redbrick import RBContext
from redbrick.common.client import RBClient
from redbrick.repo import ExportRepo


@pytest.fixture(scope="function")
def rb_context() -> RBContext:
    """Get a new mock RBClient for each test"""
    context = RBContext(
        api_key="mock_api_key_000000000000000000000000000000", url="mock_url"
    )
    return context


@pytest.fixture(scope="function")
def rb_client(rb_context) -> RBClient:
    """Get a new mock RBClient for each test"""
    return rb_context.client


@pytest.fixture(scope="function")
def mock_export_repo(rb_client):
    """Get a new mock ExportRepo object for each test"""
    export_repo = ExportRepo(rb_client)
    return export_repo
