"""Tests for `redbrick.cli.project`."""
import functools
import os
import tempfile
import uuid
from datetime import datetime
from unittest.mock import patch

import pytest

from redbrick.cli.entity import CLICache, CLIConfiguration, CLICredentials
from redbrick.cli.project import CLIProject
from redbrick.organization import RBOrganization
from redbrick.project import RBProject


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
                version = 2.13.16
            """
        )


def _write_creds(config_path, org_id, profile="mock_profile"):
    """Prepare project credentials"""
    credentials_file = os.path.join(config_path, "credentials")
    with open(credentials_file, "w", encoding="utf-8") as _creds_file:
        _creds_file.write(
            f"""[{profile}]
                key = mock_key
                org = {org_id}
                url = https://api.redbrickai.com
            """
        )
    os.environ[CLICredentials.ENV_VAR] = profile


@pytest.mark.unit
def test_init(project_and_conf_dirs):
    """Test initialization procedure"""
    project_path, config_path_ = project_and_conf_dirs
    org_id = str(uuid.uuid4())

    # prepare project config and creds
    _write_config(project_path, org_id)
    _write_creds(config_path_, org_id)

    # create CLIProject obj
    with patch("redbrick.cli.project.config_path", return_value=config_path_):
        proj = CLIProject(path=project_path)

    # assertions
    assert isinstance(proj.creds, CLICredentials)
    assert isinstance(proj.conf, CLIConfiguration)
    assert isinstance(proj.cache, CLICache)

    assert proj.creds.exists
    _profile = proj.creds.get_profile(proj.creds.selected_profile)
    assert _profile["key"] == "mock_key"
    assert _profile["org"] == org_id

    assert proj.conf.exists
    assert proj.conf.get_section("org") == {"id": org_id}
    assert proj.conf.get_option("cache", "name") is not None


@pytest.mark.unit
def test_init_no_creds(project_and_conf_dirs):
    """Test initialization procedure with missing creds"""
    project_path, config_path_ = project_and_conf_dirs
    org_id = str(uuid.uuid4())

    # prepare project config
    _write_config(project_path, org_id)

    with patch("redbrick.cli.project.config_path", return_value=config_path_):
        with pytest.raises(
            Exception,
            match="No credentials found, please set it up with `redbrick config`",
        ):
            CLIProject(path=project_path)


@pytest.mark.unit
def test_init_no_config(project_and_conf_dirs):
    """Test initialization procedure with missing config"""
    project_path, config_path_ = project_and_conf_dirs
    org_id = str(uuid.uuid4())

    # prepare project creds
    _write_creds(config_path_, org_id)

    with patch("redbrick.cli.project.config_path", return_value=config_path_):
        with pytest.raises(
            expected_exception=Exception,
            match=f"No project found in `{project_path}`\n"
            f"Please create one using `redbrick init` / clone existing using `redbrick clone`",
        ):
            CLIProject(path=project_path)


@pytest.mark.unit
def test_init_no_dir():
    """Test initialization procedure with bad directory"""
    project_path = f"{os.getcwd()}/non-existent-dir"
    with pytest.raises(Exception, match=f"Not a valid directory {project_path}"):
        CLIProject(path=project_path)


@pytest.mark.unit
def test_init_from_path(project_and_conf_dirs):
    """
    Test initialization from given path. Ensure that the right path
    with Redbrick config can be found
    """
    project_path, config_path_ = project_and_conf_dirs
    org_id = str(uuid.uuid4())

    # prepare project config and creds
    _write_config(project_path, org_id)
    _write_creds(config_path_, org_id)

    with tempfile.TemporaryDirectory(dir=project_path) as inner_dir:
        with patch("redbrick.cli.project.config_path", return_value=config_path_):
            proj = CLIProject.from_path(path=inner_dir)

        # assertions
        assert isinstance(proj.creds, CLICredentials)
        assert isinstance(proj.conf, CLIConfiguration)
        assert isinstance(proj.cache, CLICache)

        assert proj.creds.exists
        _profile = proj.creds.get_profile(proj.creds.selected_profile)
        assert _profile["key"] == "mock_key"
        assert _profile["org"] == org_id

        assert proj.conf.exists
        assert proj.conf.get_section("org") == {"id": org_id}
        assert proj.conf.get_option("cache", "name") is not None


@pytest.mark.unit
def test_initialize_project(project_and_conf_dirs, rb_context_full):
    """Test CLIProject.initialize_project"""
    project_path, config_path_ = project_and_conf_dirs
    org_id = str(uuid.uuid4())
    project_id = str(uuid.uuid4())

    # prepare project creds
    _write_creds(config_path_, org_id)

    mock_org_resp = {"name": "Mock Org", "orgId": org_id}
    mock_project_resp = {
        "status": "CREATION_SUCCESS",
        "name": "mock_project",
        "tdType": "mock_tdType",
        "taxonomy": {"name": "mock_taxonomy"},
        "workspace": {"workspaceId": uuid.uuid4()},
        "projectUrl": "mock_project_url",
        "createdAt": datetime.now().isoformat(),
        "consensusSettings": {"enabled": True},
    }
    with patch("redbrick.cli.project.config_path", return_value=config_path_):
        # mock repo methods
        rb_context_full.project.get_org = functools.partial(
            mock_method, response=mock_org_resp
        )
        rb_context_full.project.get_project = functools.partial(
            mock_method, response=mock_project_resp
        )
        rb_context_full.project.get_stages = functools.partial(mock_method, response=[])

        # initialize project
        proj = CLIProject(path=project_path, required=False)
        rb_org = RBOrganization(rb_context_full, org_id)
        rb_project = RBProject(rb_context_full, org_id, project_id)
        proj.initialize_project(rb_org, rb_project)

        # assertions
        assert isinstance(proj.creds, CLICredentials)
        assert isinstance(proj.conf, CLIConfiguration)
        assert isinstance(proj.cache, CLICache)

        assert proj.creds.exists
        _profile = proj.creds.get_profile(proj.creds.selected_profile)
        assert _profile["key"] == "mock_key"
        assert _profile["org"] == org_id

        assert proj.conf.exists
        assert proj.conf.get_section("org")["id"] == org_id
        assert proj.conf.get_section("project")["id"] == project_id
        assert proj.cache.exists


def mock_method(*args, response=None):  # pylint: disable=unused-argument
    """Stub function to help pickle mocked methods"""
    return response
