"""Tests for `redbrick.utils.rb_event_utils`."""
from typing import Dict

import pytest

from redbrick import TaskEventTypes
from redbrick.utils import rb_event_utils


@pytest.mark.unit
def test_comment_format():
    """Test a basic comment"""
    comment = {
        "commentId": 1,
        "textVal": "This is a test comment.",
        "createdBy": {"userId": "user1"},
        "stageName": "Stage 1",
        "issueComment": False,
        "issueResolved": True,
    }
    users = {"user1": "John Doe"}
    formatted_comment = rb_event_utils.comment_format(comment, users)
    assert formatted_comment == {
        "commentId": 1,
        "commentText": "This is a test comment.",
        "createdBy": "John Doe",
        "stage": "Stage 1",
        "isIssue": False,
        "issueResolved": True,
    }


@pytest.mark.unit
def test_task_event_format():
    """Test a task creation event"""
    task: Dict = {
        "genericEvents": [
            {
                "__typename": "TaskEvent",
                "createEvent": {
                    "isGroundTruth": False,
                    "currentStageName": "Label",
                },
                "taskData": {"createdBy": "user1"},
                "createdAt": "2023-10-20T14:31:44.252197+00:00",
            }
        ],
        "taskId": 1,
        "datapoint": {"name": "Test Task"},
        "currentStageName": "Stage 1",
    }
    users = {"user1": "John Doe"}
    formatted_task_event = rb_event_utils.task_event_format(task, users)
    assert (
        formatted_task_event["events"][0]["eventType"]
        == TaskEventTypes.TASK_CREATED.value
    )
    assert formatted_task_event["events"][0]["isGroundTruth"] is False
    assert formatted_task_event["events"][0]["createdBy"] == "John Doe"

    # Test a task event with a comment
    task["genericEvents"].append(
        {
            "__typename": "Comment",
            "commentId": 2,
            "textVal": "This is a comment on the task.",
            "createdBy": {"userId": "user2"},
            "stageName": "Stage 2",
            "issueComment": False,
            "issueResolved": True,
            "replies": [],
            "createdAt": "2023-10-20T14:31:44.252197+00:00",
        }
    )
    users["user2"] = "Jane Smith"
    formatted_task_event = rb_event_utils.task_event_format(task, users)
    assert (
        formatted_task_event["events"][1]["eventType"]
        == TaskEventTypes.COMMENT_ADDED.value
    )
    assert formatted_task_event["events"][1]["commentId"] == 2
    assert (
        formatted_task_event["events"][1]["commentText"]
        == "This is a comment on the task."
    )
    assert formatted_task_event["events"][1]["createdBy"] == "Jane Smith"
    assert formatted_task_event["events"][1]["stage"] == "Stage 2"
    assert formatted_task_event["events"][1]["isIssue"] is False
    assert formatted_task_event["events"][1]["issueResolved"] is True


@pytest.mark.unit
def test_task_event_format_additional_paths():
    """Test a task event with a task acceptance"""
    task = {
        "genericEvents": [
            {
                "__typename": "TaskEvent",
                "outputEvent": {
                    "outputBool": True,
                    "currentStageName": "Review",
                },
                "taskData": {"createdBy": "user1"},
                "createdAt": "2023-10-20T14:31:44.252197+00:00",
            }
        ],
        "taskId": 1,
        "datapoint": {"name": "Test Task"},
        "currentStageName": "Review",
    }
    users = {"user1": "John Doe"}
    formatted_task_event = rb_event_utils.task_event_format(task, users)
    assert (
        formatted_task_event["events"][0]["eventType"]
        == TaskEventTypes.TASK_ACCEPTED.value
    )
    assert formatted_task_event["events"][0]["stage"] == "Review"
    assert formatted_task_event["events"][0]["updatedBy"] == "John Doe"

    # Test a task event with a task rejection
    task["genericEvents"][0]["outputEvent"]["outputBool"] = False
    formatted_task_event = rb_event_utils.task_event_format(task, users)
    assert (
        formatted_task_event["events"][0]["eventType"]
        == TaskEventTypes.TASK_REJECTED.value
    )

    # Test a task event with a consensus task edited
    task = {
        "genericEvents": [
            {
                "__typename": "TaskStateChanges",
                "consensusAssigneesBefore": ["user1"],
                "consensusAssigneesAfter": ["user2"],
                "consensusStatusesBefore": ["IN_PROGRESS"],
                "consensusStatusesAfter": ["SKIPPED"],
                "stageNameAfter": "Review",
                "assignedToAfter": "user3",
                "createdAt": "2023-10-20T14:31:44.252197+00:00",
            }
        ],
        "taskId": 1,
        "datapoint": {"name": "Test Task"},
        "currentStageName": "Review",
    }
    users = {"user1": "John Doe", "user2": "Jane Smith"}
    formatted_task_event = rb_event_utils.task_event_format(task, users)
    assert (
        formatted_task_event["events"][0]["eventType"]
        == TaskEventTypes.CONSENSUS_TASK_EDITED.value
    )
    assert (
        formatted_task_event["events"][0]["consensusUsers"][0]["assignee"]
        == "Jane Smith"
    )
    assert formatted_task_event["events"][0]["consensusUsers"][0]["status"] == "SKIPPED"
    assert (
        formatted_task_event["events"][0]["prevConsensusUsers"][0]["assignee"]
        == "John Doe"
    )
    assert (
        formatted_task_event["events"][0]["prevConsensusUsers"][0]["status"]
        == "IN_PROGRESS"
    )
