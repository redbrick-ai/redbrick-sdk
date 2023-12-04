"""Tests for `redbrick.cli.command.upload`."""
import argparse
from unittest.mock import patch

import pytest

from redbrick.cli import public, CLIProject


@pytest.mark.unit
def test_handler(prepare_project, monkeypatch):
    """Test `CLIUploadController.handler` correctly gets project details"""
    project_path, config_path_, _, _ = prepare_project
    monkeypatch.chdir(project_path)
    _, cli = public.cli_parser(only_parser=False)

    with patch(
        "redbrick.cli.project.config_path", return_value=config_path_
    ), patch.object(cli.upload, "handle_upload") as _handle_upload:
        args = argparse.Namespace(command=cli.CLONE, path=project_path)
        cli.upload.handler(args)
        _handle_upload.assert_called_once()
        assert isinstance(cli.upload.project, CLIProject)
