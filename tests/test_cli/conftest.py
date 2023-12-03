"""Pytest Fixtures for tests in test.test_cli"""
import os
import shutil
import typing as t

import pytest


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
