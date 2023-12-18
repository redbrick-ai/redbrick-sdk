"""Tests for `redbrick.cli.command.report`."""
import argparse
import os
from unittest.mock import patch, Mock

import pytest

from redbrick.cli import public, CLIProject
from redbrick.cli.command import CLIIReportController


@pytest.mark.unit
def test_handler(prepare_project, monkeypatch):
    """Test `CLIIReportController.handler` correctly gets project details"""
    project_path, config_path_, _, _ = prepare_project
    monkeypatch.chdir(project_path)
    _, cli = public.cli_parser(only_parser=False)

    with patch(
        "redbrick.cli.project.config_path", return_value=config_path_
    ), patch.object(cli.report, "handle_report"):
        args = argparse.Namespace(
            type=cli.report.TYPE_ALL,
            concurrency=10,
        )
        cli.report.handler(args)
        cli.report.handle_report.assert_called_once()
        assert isinstance(cli.report.project, CLIProject)


@pytest.mark.unit
def test_handle_report(
    mock_report_controller, monkeypatch, capsys
):  # pylint: disable=too-many-locals
    """Test the `CLIIReportController.handle_report`"""
    controller: CLIIReportController
    controller, project_path, _ = mock_report_controller
    monkeypatch.chdir(project_path)

    mock_get_members = Mock(
        return_value=[
            {"member": {"user": {"userId": "mock_user_id", "email": "mock@email.com"}}},
        ]
    )
    mock_task_events = [
        {
            "genericEvents": [
                {
                    "__typename": "TaskEvent",
                    "eventId": "35bc57ee-44c8-476f-82db-eec3968a99df",
                    "createdAt": "2023-10-20T14:33:27.971766+00:00",
                    "inputEvent": None,
                    "outputEvent": {
                        "currentStageName": "Label",
                        "outputBool": None,
                    },
                    "createEvent": None,
                    "taskData": {
                        "stageName": "Label",
                        "createdBy": "1c643889-5a8b-4b20-8e48-14e9cbd5eeb7",
                    },
                },
                {
                    "__typename": "TaskStateChanges",
                    "stageNameAfter": "Review_1",
                    "assignedAtAfter": "2023-10-20T14:32:53.350676+00:00",
                    "createdAt": "2023-10-20T14:33:01.540533+00:00",
                    "statusBefore": "ASSIGNED",
                    "statusAfter": "COMPLETED",
                    "assignedToBefore": "1c643889-5a8b-4b20-8e48-14e9cbd5eeb7",
                    "assignedToAfter": "1c643889-5a8b-4b20-8e48-14e9cbd5eeb7",
                    "consensusAssigneesBefore": [],
                    "consensusAssigneesAfter": [],
                    "consensusStatusesBefore": [],
                    "consensusStatusesAfter": [],
                },
            ],
            "taskId": "mock_task_id",
            "datapoint": {"name": "mock_dp_name"},
            "currentStageName": "Review",
        },
    ]

    mock_task_events = Mock(return_value=(mock_task_events, None))
    with patch.object(
        controller.project.project.context.project,
        "get_members",
        mock_get_members,
    ), patch.object(
        controller.project.project.context.export,
        "task_events",
        mock_task_events,
    ):
        controller.args = argparse.Namespace(type=controller.TYPE_ALL, concurrency=10)
        # call method
        controller.handle_report()
        output = capsys.readouterr()
        assert "Exported successfully to:" in output.out

        report_found = False
        for filename in os.listdir(project_path):
            if filename.startswith("report-") and filename.endswith(".json"):
                if not report_found:
                    report_found = True
                else:
                    raise AssertionError("More than one report file created")
        assert report_found
