"""Pytest Fixtures for tests in test.test_cli"""
import argparse
import functools
import os
import shutil
import typing as t
import uuid
from datetime import datetime
from unittest.mock import patch

import pytest

from redbrick import RBContext
from redbrick.cli import public
from redbrick.cli.command import (
    CLIExportController,
    CLIUploadController,
    CLIIReportController,
)
from tests.test_cli import _write_config, _write_creds, mock_method


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
def prepare_project(
    project_and_conf_dirs, rb_context_full  # pylint:disable=redefined-outer-name
) -> t.Tuple[str, str, str, str]:
    """Fixture to prepare all dirs and config for a project"""
    project_path, config_path_ = project_and_conf_dirs
    org_id = str(uuid.uuid4())
    project_id = str(uuid.uuid4())

    # prepare project config and creds
    _write_config(project_path, org_id, project_id=project_id)
    _write_creds(config_path_, org_id, api_key=rb_context_full.client.api_key)
    return project_path, config_path_, org_id, project_id


@pytest.fixture
def mock_cli_rb_context(
    prepare_project,  # pylint: disable=redefined-outer-name
    rb_context_full,
) -> t.Tuple[RBContext, t.Tuple[str, str, str, str]]:
    """Prepare a test RBContext object with patched query methods"""
    _, _, org_id, project_id = prepare_project
    project_name = "real_project"

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
    return rb_context_full, prepare_project


@pytest.fixture
def mock_upload_controller(
    mock_cli_rb_context,  # pylint: disable=redefined-outer-name
    monkeypatch,
) -> t.Tuple[CLIUploadController, str]:
    """Prepare a test CLIUploadController object"""
    # attache project to cli controller
    # pylint: disable=redefined-outer-name
    rb_context_full, prepare_project = mock_cli_rb_context
    project_path, config_path_, _, _ = prepare_project
    # pylint: enable=redefined-outer-name
    monkeypatch.chdir(project_path)
    _, cli = public.cli_parser(only_parser=False)

    handle_upload = cli.upload.handle_upload
    with patch("redbrick.cli.project.config_path", return_value=config_path_), patch(
        "redbrick.cli.command.clone.CLIProject._context", rb_context_full
    ), patch.object(cli.upload, "handle_upload"):
        args = argparse.Namespace(command=cli.CLONE)
        cli.upload.handler(args)
        _ = cli.upload.project.project
        controller = cli.upload

    controller.handle_upload = handle_upload
    return controller, project_path


@pytest.fixture
def mock_export_controller(
    mock_cli_rb_context,  # pylint: disable=redefined-outer-name
    monkeypatch,
) -> t.Tuple[CLIExportController, str]:
    """Prepare a test CLIExportController object"""
    # attach project to cli controller
    # pylint: disable=redefined-outer-name
    rb_context_full, prepare_project = mock_cli_rb_context
    project_path, config_path_, _, _ = prepare_project
    # pylint: enable=redefined-outer-name
    monkeypatch.chdir(project_path)
    _, cli = public.cli_parser(only_parser=False)

    handle_export = cli.export.handle_export
    with patch("redbrick.cli.project.config_path", return_value=config_path_), patch(
        "redbrick.cli.command.export.CLIProject._context", rb_context_full
    ), patch.object(cli.export, "handle_export"):
        args = argparse.Namespace(command=cli.CLONE)
        cli.export.handler(args)
        _ = cli.export.project.project
        controller = cli.export

    controller.handle_export = handle_export
    return controller, project_path


@pytest.fixture
def mock_info_controller(
    mock_cli_rb_context,  # pylint: disable=redefined-outer-name
    monkeypatch,
) -> t.Tuple[CLIExportController, str, str]:
    """Prepare a test CLIInfoController object"""
    # attach project to cli controller
    # pylint: disable=redefined-outer-name
    rb_context_full, prepare_project = mock_cli_rb_context
    project_path, config_path_, _, _ = prepare_project
    # pylint: enable=redefined-outer-name
    monkeypatch.chdir(project_path)
    _, cli = public.cli_parser(only_parser=False)

    handle_info = cli.info.handle_info
    with patch("redbrick.cli.project.config_path", return_value=config_path_), patch(
        "redbrick.cli.command.info.CLIProject._context", rb_context_full
    ), patch.object(cli.info, "handle_info"):
        args = argparse.Namespace(command=cli.INFO, path=".", get=None, set=None)
        cli.info.handler(args)
        _ = cli.info.project.project
        _ = cli.info.project.org
        controller = cli.info

    controller.handle_info = handle_info
    return controller, project_path, config_path_


@pytest.fixture
def mock_report_controller(
    mock_cli_rb_context,  # pylint: disable=redefined-outer-name
    monkeypatch,
) -> t.Tuple[CLIIReportController, str, str]:
    """Prepare a test CLIIReportController object"""
    # attach project to cli controller
    # pylint: disable=redefined-outer-name
    rb_context_full, prepare_project = mock_cli_rb_context
    project_path, config_path_, _, _ = prepare_project
    # pylint: enable=redefined-outer-name
    monkeypatch.chdir(project_path)
    _, cli = public.cli_parser(only_parser=False)

    handle_report = cli.report.handle_report
    with patch("redbrick.cli.project.config_path", return_value=config_path_), patch(
        "redbrick.cli.command.report.CLIProject._context", rb_context_full
    ), patch.object(cli.report, "handle_report"):
        args = argparse.Namespace(command=cli.INFO, path=".", get=None, set=None)
        cli.report.handler(args)
        _ = cli.report.project.project
        controller = cli.report

    controller.handle_report = handle_report
    return controller, project_path, config_path_
