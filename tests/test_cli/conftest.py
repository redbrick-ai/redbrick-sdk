"""Pytest Fixtures for tests in test.test_cli"""
import os
import shutil
import typing as t
import uuid

import pytest

from tests.test_cli import _write_config, _write_creds


@pytest.fixture
def project_and_conf_dirs(
    tmpdir,
) -> t.Generator[t.Tuple[str, str], None, None]:  # noqa
    """Prepare mock project dir and conf dir"""
    project_path = os.path.join(str(tmpdir), "mock_project")
    os.mkdir(project_path)

    credentials_path = os.path.join(str(tmpdir), "mock_creds")
    os.makedirs(credentials_path)

    yield project_path, credentials_path
    shutil.rmtree(project_path, ignore_errors=True)
    shutil.rmtree(credentials_path, ignore_errors=True)


@pytest.fixture
def prepare_project(project_and_conf_dirs, rb_context_full):
    project_path, config_path_ = project_and_conf_dirs
    org_id = str(uuid.uuid4())
    project_id = str(uuid.uuid4())

    # prepare project config and creds
    _write_config(project_path, org_id, project_id=project_id)
    _write_creds(config_path_, org_id, api_key=rb_context_full.client.api_key)
    return project_path, config_path_, org_id, project_id
