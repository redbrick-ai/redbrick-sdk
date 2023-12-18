"""tests.test_cli module"""
import os
import uuid
from datetime import datetime

from redbrick.cli.entity import CLICredentials


def _write_config(project_path: str, org_id: str, project_id: str = str(uuid.uuid4())):
    """Prepare project config"""
    _redbrick_pth = os.path.join(project_path, ".redbrick")
    os.makedirs(_redbrick_pth)
    with open(
        os.path.join(_redbrick_pth, "config"), "w", encoding="utf-8"
    ) as _conf_file:
        _conf_file.write(
            f"""[org]
                id = {org_id}
                [project]
                id = {project_id}
                refresh = {datetime.now()}
                version = 2.13.20
            """
        )


def _write_creds(
    config_path,
    org_id,
    profile="mock_profile",
    api_key="mock_key",
    url="https://api.redbrickai.com",
):
    """Prepare project credentials"""
    credentials_file = os.path.join(config_path, "credentials")
    with open(credentials_file, "w", encoding="utf-8") as _creds_file:
        _creds_file.write(
            f"""[{profile}]
                key = {api_key}
                org = {org_id}
                url = {url}
                [default]
                profile = {profile}
            """
        )


def mock_method(*args, response=None):  # pylint: disable=unused-argument
    """Stub function to help enable pickling of mocked methods"""
    return response
