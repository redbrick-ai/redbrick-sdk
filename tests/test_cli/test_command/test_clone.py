"""Tests for `redbrick.cli.command.clone`."""
import argparse
import functools
import os
import re
import uuid
from datetime import datetime
from unittest.mock import patch

import pytest

from redbrick.cli import public
from tests.test_cli import _write_config, _write_creds, mock_method


@pytest.mark.unit
def test_clone_handler__existing_project(project_and_conf_dirs, monkeypatch):
    """Ensure project clones fail when run in an existing project/dir"""
    project_path, config_path_ = project_and_conf_dirs
    org_id = str(uuid.uuid4())

    _, cli = public.cli_parser(only_parser=False)

    with pytest.raises(Exception, match=re.escape(f"{project_path} already exists")):
        args = argparse.Namespace(command=cli.CLONE, path=project_path)
        cli.clone.handler(args)

    # prepare project config and creds
    _write_config(project_path, org_id)
    _write_creds(config_path_, org_id)

    monkeypatch.chdir(project_path)
    with pytest.raises(Exception, match="Already inside a project"):
        args = argparse.Namespace(command=cli.CLONE, path=None)
        cli.clone.handler(args)


@pytest.mark.unit
def test_handler(tmpdir):
    """Test `CLICloneController.handler`"""
    project_dir = os.path.join(str(tmpdir), "project")
    _, cli = public.cli_parser(only_parser=False)

    with patch.object(cli.clone, "handle_clone"):
        args = argparse.Namespace(command=cli.CLONE, path=project_dir)
        cli.clone.handler(args)
        cli.clone.handle_clone.assert_called_once()


@pytest.mark.unit
@pytest.mark.parametrize("select_by_id", [True, False])
def test_handle_clone(
    project_and_conf_dirs, rb_context_full, monkeypatch, select_by_id
):
    """Test `CLICloneController.handle_clone`"""
    project_path, config_path_ = project_and_conf_dirs
    monkeypatch.chdir(project_path)
    org_id = str(uuid.uuid4())
    project_id = str(uuid.uuid4())
    project_name = "real_project"

    # prepare project config and creds
    _write_config(project_path, org_id, project_id=project_id)
    _write_creds(config_path_, org_id, api_key=rb_context_full.client.api_key)

    _, cli = public.cli_parser(only_parser=False)

    # mock repo methods
    # pylint: disable=protected-access
    mock_org_resp = {"name": "Mock Org", "orgId": org_id}
    mock_projects_resp = [
        {
            "status": "CREATION_SUCCESS",
            "projectId": project_id,
            "name": project_name,
            "tdType": "mock_tdType",
            "taxonomy": {"name": "mock_taxonomy"},
            "workspace": {"workspaceId": uuid.uuid4()},
            "projectUrl": "mock_project_url",
            "createdAt": datetime.now().isoformat(),
            "consensusSettings": {"enabled": True},
        }
    ]
    rb_context_full.project.get_org = functools.partial(
        mock_method, response=mock_org_resp
    )
    rb_context_full.project.get_project = functools.partial(
        mock_method, response=mock_projects_resp[0]
    )
    rb_context_full.project.get_projects = functools.partial(
        mock_method, response=mock_projects_resp
    )
    rb_context_full.project.get_stages = functools.partial(mock_method, response=[])
    # pylint: enable=protected-access

    with patch("redbrick.cli.project.config_path", return_value=config_path_), patch(
        "redbrick.cli.command.clone.CLIProject._context", rb_context_full
    ):
        _project_desc = project_id if select_by_id else project_name
        cli.clone.args = argparse.Namespace(
            command=cli.CLONE, path=None, project=_project_desc
        )
        cli.clone.handle_clone()

    assert os.path.isdir(os.path.join(project_path, ".redbrick"))
    real_project_path = os.path.join(project_path, project_name)
    assert os.path.exists(real_project_path)
    assert os.path.isdir(os.path.join(real_project_path, ".redbrick", "cache"))
    assert os.path.isfile(os.path.join(real_project_path, ".redbrick", "config"))
