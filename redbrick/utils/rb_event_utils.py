"""Utilities for working with event objects."""
from typing import Optional, List, Dict

from redbrick.common.enums import TaskEventTypes


def user_format(user: Optional[str], users: Dict[str, str]) -> Optional[str]:
    """User format."""
    if not user:
        return user
    if user.startswith("RB:"):
        return "System"
    if user.startswith("API:"):
        return "API Key"
    return users.get(user, user)


def comment_format(comment: Dict, users: Dict[str, str]) -> Dict:
    """Comment format."""
    return {
        "commentId": comment["commentId"],
        "commentText": comment["textVal"],
        "createdBy": user_format(comment["createdBy"]["userId"], users),
        "stage": comment["stageName"],
        "isIssue": comment["issueComment"],
        "issueResolved": comment["issueResolved"],
    }


def task_event_format(task: Dict, users: Dict[str, str]) -> Dict:
    """Convert task to event format."""
    # pylint: disable=too-many-branches, too-many-statements
    events: List[Dict] = []
    prev_stage = None
    prev_assignee = None
    last_pos = -1
    type_pos: Dict[TaskEventTypes, int] = {}

    for task_event in task["genericEvents"]:
        event_type = None
        event = {}
        if task_event["__typename"] == "TaskEvent":
            if task_event.get("createEvent"):
                event_type = TaskEventTypes.TASK_CREATED
                event["isGroundTruth"] = task_event["createEvent"]["isGroundTruth"]
                if task_event["taskData"]:
                    event["createdBy"] = user_format(
                        task_event["taskData"]["createdBy"], users
                    )
                prev_stage = task_event["createEvent"]["currentStageName"]
            elif task_event.get("inputEvent"):
                if task_event["inputEvent"].get("overallConsensusScore") is not None:
                    event_type = TaskEventTypes.CONSENSUS_COMPUTED
                    event["stage"] = prev_stage
                    event["score"] = task_event["inputEvent"]["overallConsensusScore"]
                prev_stage = task_event["inputEvent"]["currentStageName"]
            elif task_event.get("outputEvent"):
                if task_event["outputEvent"]["currentStageName"] not in (
                    "Failed_Review",
                    "Output",
                ):
                    if task_event["outputEvent"]["currentStageName"] == "END":
                        event_type = TaskEventTypes.GROUNDTRUTH_TASK_EDITED
                        event["updatedBy"] = user_format(
                            task_event["taskData"]["createdBy"], users
                        )
                    else:
                        event_type = (
                            TaskEventTypes.TASK_SUBMITTED
                            if task_event["outputEvent"]["outputBool"] is None
                            else TaskEventTypes.TASK_ACCEPTED
                            if task_event["outputEvent"]["outputBool"]
                            else TaskEventTypes.TASK_REJECTED
                        )
                        event["stage"] = task_event["outputEvent"]["currentStageName"]
                        event["updatedBy"] = user_format(
                            prev_assignee or task_event["taskData"]["createdBy"], users
                        )
                prev_stage = task_event["outputEvent"]["currentStageName"]

        elif task_event["__typename"] == "Comment":
            event_type = TaskEventTypes.COMMENT_ADDED
            event.update(comment_format(task_event, users))
            event["replies"] = [
                comment_format(reply, users) for reply in task_event["replies"]
            ]
            prev_stage = event["stage"]
        elif task_event["__typename"] == "TaskStateChanges":
            if (
                task_event["consensusAssigneesBefore"]
                != task_event["consensusAssigneesAfter"]
                or task_event["consensusStatusesBefore"]
                != task_event["consensusStatusesAfter"]
            ):
                event_type = TaskEventTypes.CONSENSUS_TASK_EDITED
                event["consensusUsers"] = [
                    {"assignee": user_format(assignee, users), "status": status}
                    for assignee, status in zip(
                        task_event["consensusAssigneesAfter"],
                        task_event["consensusStatusesAfter"],
                    )
                ]
                event["prevConsensusUsers"] = [
                    {"assignee": user_format(assignee, users), "status": status}
                    for assignee, status in zip(
                        task_event["consensusAssigneesBefore"],
                        task_event["consensusStatusesBefore"],
                    )
                ]

            elif task_event["assignedToBefore"] != task_event["assignedToAfter"]:
                if not task_event["assignedToAfter"]:
                    event_type = TaskEventTypes.TASK_UNASSIGNED
                    event["prevAssignee"] = user_format(
                        task_event["assignedToBefore"], users
                    )
                elif task_event["assignedToBefore"]:
                    event_type = TaskEventTypes.TASK_REASSIGNED
                    event["assignee"] = user_format(
                        task_event["assignedToAfter"], users
                    )
                    event["prevAssignee"] = user_format(
                        task_event["assignedToBefore"], users
                    )
                else:
                    event_type = TaskEventTypes.TASK_ASSIGNED
                    event["assignee"] = user_format(
                        task_event["assignedToAfter"], users
                    )

            elif task_event["statusBefore"] != task_event["statusAfter"]:
                if task_event["statusAfter"] == "SKIPPED":
                    event_type = TaskEventTypes.TASK_SKIPPED
                    event["assignee"] = user_format(
                        task_event["assignedToAfter"], users
                    )
                elif task_event["statusAfter"] == "IN_PROGRESS" and task_event[
                    "statusBefore"
                ] in ("SKIPPED", "ASSIGNED"):
                    event_type = TaskEventTypes.TASK_SAVED
                    event["assignee"] = user_format(
                        task_event["assignedToAfter"], users
                    )
                    if type_pos.get(TaskEventTypes.TASK_SAVED, -1) >= 0:
                        events.pop(type_pos[TaskEventTypes.TASK_SAVED])
                        last_pos -= 1

            event["stage"] = task_event["stageNameAfter"] or prev_stage

            if task_event["stageNameAfter"]:
                prev_stage = task_event["stageNameAfter"]

            prev_assignee = task_event["assignedToAfter"]

        if event_type:
            events.append(
                {
                    "eventType": event_type.value,
                    "createdAt": task_event["createdAt"],
                    **event,
                }
            )
            last_pos += 1
            type_pos[event_type] = last_pos

    if 0 <= type_pos.get(TaskEventTypes.TASK_SAVED, -1) != last_pos >= 0:
        events.pop(type_pos[TaskEventTypes.TASK_SAVED])
        last_pos -= 1

    return {
        "taskId": task["taskId"],
        "taskName": task["datapoint"]["name"],
        "currentStageName": task["currentStageName"],
        "events": sorted(events, key=lambda evt: evt.get("createdAt", "") or ""),
    }
