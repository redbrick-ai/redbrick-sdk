import pytest

from redbrick.repo import ExportRepo


@pytest.fixture(scope="function")
def mock_export_repo(request, rb_client):
    export_repo = ExportRepo(rb_client)
    return export_repo
