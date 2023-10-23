import pytest

from redbrick.common.client import RBClient


@pytest.fixture(scope="function")
def rb_client(request):
    client = RBClient(api_key="mock_api_key_000000000000000000000000000000", url="mock_url")
    return client
