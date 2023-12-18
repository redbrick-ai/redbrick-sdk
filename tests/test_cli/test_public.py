"""Tests for `redbrick.cli.public`."""
import argparse
import typing as t
from unittest.mock import Mock, patch

import pytest

from redbrick.cli import public
from redbrick.cli.cli_base import CLIInterface
from redbrick.cli.command import (
    CLIConfigController,
    CLIInitController,
    CLICloneController,
    CLIInfoController,
    CLIExportController,
    CLIUploadController,
    CLIIReportController,
)

cli_controller_lookup: t.Dict[str, t.Tuple[str, t.Type]] = {
    "config": ("CONFIG", CLIConfigController),
    "init": ("INIT", CLIInitController),
    "clone": ("CLONE", CLICloneController),
    "info": ("INFO", CLIInfoController),
    "export": ("EXPORT", CLIExportController),
    "upload": ("UPLOAD", CLIUploadController),
    "report": ("REPORT", CLIIReportController),
}


@pytest.mark.unit
def test_cli_controller_init():
    """Test CLIController initialization"""
    _, cli = public.cli_parser(only_parser=False)
    assert isinstance(cli, public.CLIController)
    assert isinstance(cli, CLIInterface)

    for _ctrl_key, (_command, _expected_controller) in cli_controller_lookup.items():
        assert hasattr(cli, _ctrl_key)
        assert hasattr(cli, _command)

        command = getattr(cli, _command, None)
        assert isinstance(command, str)

        sub_controller = getattr(cli, _ctrl_key, None)
        assert isinstance(sub_controller, _expected_controller)


@pytest.mark.unit
@pytest.mark.parametrize("method_name", sorted(cli_controller_lookup))
def test_cli_controller_command_handler(method_name):
    """Ensure `handle_command` calls the right sub-controller"""
    _, cli = public.cli_parser(only_parser=False)
    # mock method
    mock_method = Mock()
    setattr(cli, method_name, mock_method)
    # create argument
    args = argparse.Namespace(command=method_name)
    # call method
    cli.handle_command(args)
    # assertion
    mock_method.handler.assert_called_once_with(args)


@pytest.mark.unit
def test_main_parser():
    """Test arg parser initialization"""
    parser = public.cli_parser()
    assert isinstance(parser, argparse.ArgumentParser)

    # pylint: disable=protected-access
    help_found = False
    version_found = False
    sub_parsers_actions: t.Optional[argparse._SubParsersAction] = None

    for _action in parser._actions:
        if isinstance(_action, argparse._HelpAction):
            if help_found:
                raise AssertionError("Duplicate HelpAction found in parser")
            help_found = True
        elif isinstance(_action, argparse._VersionAction):
            if version_found:
                raise AssertionError("Duplicate VersionAction found in parser")
            version_found = True
        elif isinstance(_action, argparse._SubParsersAction):
            if sub_parsers_actions is not None:
                raise AssertionError("Duplicate SubParsersAction found in parser")
            sub_parsers_actions = _action

    # pylint: enable=protected-access

    assert sub_parsers_actions.container.title == "Commands"
    assert isinstance(sub_parsers_actions.choices, dict)

    parser_cmds = set(sub_parsers_actions.choices)
    controller_cmds = set(cli_controller_lookup)
    _prs_diff = parser_cmds - controller_cmds
    _ctr_diff = controller_cmds - parser_cmds
    assert len(_prs_diff) == 0, f"CLI Parser has unimplemented commands: {_prs_diff}"
    assert len(_ctr_diff) == 0, f"CLI Controller has unexposed commands: {_ctr_diff}"


@pytest.mark.unit
def test_cli_main(capsys, prepare_project):
    """Test main cli entrypoint with different inputs"""
    _, config_path_, _, _ = prepare_project

    argv = ["--help"]
    expected_help_text = (
        "The RedBrick CLI offers a simple interface to quickly import and export your\n"
        "images & annotations, and perform other high-level actions."
    )
    with pytest.raises(SystemExit):
        public.cli_main(argv)
    output = capsys.readouterr()
    assert expected_help_text in output.out

    argv = ["help"]
    expected_error_text = "invalid choice: 'help'"
    with pytest.raises(SystemExit):
        public.cli_main(argv)
    output = capsys.readouterr()
    assert expected_error_text in output.err

    argv = []
    public.cli_main(argv)
    output = capsys.readouterr()
    assert "ArgumentError" in output.out

    with patch("redbrick.cli.project.config_path", return_value=config_path_):
        argv = ["config", "list"]
        expected_text = "RedBrick AI Profiles"
        public.cli_main(argv)
        output = capsys.readouterr()
        assert expected_text in output.out
