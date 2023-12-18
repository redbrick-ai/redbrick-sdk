"""Tests for `redbrick.cli.command.info`."""
import argparse
from unittest.mock import patch, Mock

import pytest

from redbrick import StorageMethod
from redbrick.cli import public, CLIProject
from redbrick.cli.command import CLIInfoController


@pytest.mark.unit
def test_handler(prepare_project, monkeypatch):
    """Test `CLIInfoController.handler` correctly gets project details"""
    project_path, config_path_, _, _ = prepare_project
    monkeypatch.chdir(project_path)
    _, cli = public.cli_parser(only_parser=False)

    with patch(
        "redbrick.cli.project.config_path", return_value=config_path_
    ), patch.object(cli.info, "handle_get"), patch.object(
        cli.info, "handle_set"
    ), patch.object(
        cli.info, "handle_info"
    ):
        args = argparse.Namespace(
            command=cli.INFO, path=project_path, get=None, set=None
        )
        cli.info.handler(args)
        cli.info.handle_info.assert_called_once()

        args = argparse.Namespace(
            command=cli.INFO, path=project_path, get="mock", set=None
        )
        cli.info.handler(args)
        cli.info.handle_get.assert_called_once()

        args = argparse.Namespace(
            command=cli.INFO, path=project_path, get=None, set="mock"
        )
        cli.info.handler(args)
        cli.info.handle_set.assert_called_once()

        assert isinstance(cli.info.project, CLIProject)


@pytest.mark.unit
def test_handle_get(
    mock_info_controller, monkeypatch, capsys
):  # pylint: disable=too-many-locals
    """Test the `CLIInfoController.handle_get`"""
    controller: CLIInfoController
    controller, project_path, _ = mock_info_controller
    monkeypatch.chdir(project_path)

    with patch.object(
        controller.project.project.context.project,
        "get_label_storage",
        return_value=("mock_storage_id", "mock_path"),
    ):
        controller.args = argparse.Namespace(get="labelstorage", path=".")
        # call method
        controller.handle_get()
        output = capsys.readouterr()
        assert "mock_storage_id" in output.out
        assert "mock_path" in output.out


@pytest.mark.unit
def test_handle_set(
    mock_info_controller, monkeypatch, capsys
):  # pylint: disable=too-many-locals
    """Test the `CLIInfoController.handle_set`"""
    controller: CLIInfoController
    controller, project_path, _ = mock_info_controller
    monkeypatch.chdir(project_path)

    mock_repo_setter = Mock(return_value=False)
    with patch.object(
        controller.project.project.context.project,
        "set_label_storage",
        mock_repo_setter,
    ), patch(
        "redbrick.cli.input.uuid.CLIInputUUID.get", return_value=StorageMethod.PUBLIC
    ), patch(
        "redbrick.cli.input.text.CLIInputText.get", return_value="mock_path"
    ):

        controller.args = argparse.Namespace(get=None, set="labelstorage", path=".")
        # call method
        controller.handle_set()
        output = capsys.readouterr()
        assert StorageMethod.PUBLIC in output.out
        assert "mock_path" in output.out
        mock_repo_setter.assert_called_once()


@pytest.mark.unit
def test_handle_info(
    mock_cli_rb_context, monkeypatch, capsys
):  # pylint: disable=too-many-locals
    """Test the `CLIInfoController.handle_info`"""
    rb_context_full, prepare_project = mock_cli_rb_context
    project_path, config_path_, org_id, project_id = prepare_project
    monkeypatch.chdir(project_path)
    _, cli = public.cli_parser(only_parser=False)
    controller: CLIInfoController = cli.info

    with patch("redbrick.cli.project.config_path", return_value=config_path_), patch(
        "redbrick.cli.command.info.CLIProject._context", rb_context_full
    ):
        args = argparse.Namespace(
            command=cli.INFO, path=project_path, get=None, set=None
        )
        # call method (through main entrypoint)
        controller.handler(args)
        output = capsys.readouterr()
        assert org_id in output.out
        assert project_id in output.out
        assert "Mock Org" in output.out
        assert "real_project" in output.out
        assert "mock_taxonomy" in output.out
        assert "mock_project_url" in output.out
