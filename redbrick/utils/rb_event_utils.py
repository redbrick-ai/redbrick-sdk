"""Utilities for working with event objects."""

import json
from typing import List, Dict

from typing import Optional

from redbrick.common.enums import TaskEventTypes
from redbrick.utils.rb_label_utils import clean_rb_label, flat_rb_format, user_format


def comment_format(comment: Dict, users: Dict[str, str]) -> Dict:
    """Comment format."""
    comment_obj = {
        "commentId": comment["commentId"],
        "commentText": comment["textVal"],
        "createdBy": user_format(comment["createdBy"], users),
        "stage": comment["stageName"],
        "isIssue": comment["issueComment"],
        "issueResolved": comment["issueResolved"],
    }

    if comment.get("labelEntityLabelId"):
        comment_obj["labelId"] = comment["labelEntityLabelId"]

    if comment.get("pin"):
        comment_obj["pin"] = {
            "pinId": comment["pin"]["pinId"],
            "pointX": comment["pin"]["pointX"],
            "pointY": comment["pin"]["pointY"],
            "pointZ": comment["pin"]["pointZ"],
            "frameIndex": comment["pin"]["frameIndex"],
            "volumeIndex": comment["pin"]["volumeIndex"],
        }

    return comment_obj


def task_event_format(
    task: Dict, users: Dict[str, str], with_labels: bool = False
) -> Dict:
    """Convert task to event format."""
    # pylint: disable=too-many-branches, too-many-statements, too-many-locals
    events: List[Dict] = []
    prev_stage = None
    prev_assignee = None
    last_pos = -1
    type_pos: Dict[TaskEventTypes, int] = {}
    review_result = True

    for task_event in task["genericEvents"]:
        event_type = None
        event = {}
        if task_event["__typename"] == "TaskEvent":
            if task_event.get("createEvent"):
                event_type = TaskEventTypes.TASK_CREATED
                event["isGroundTruth"] = task_event["createEvent"]["isGroundTruth"]
                if task_event["createEvent"].get("priority") is not None:
                    event["priority"] = task_event["createEvent"]["priority"]
                if task_event["taskData"]:
                    event["createdBy"] = user_format(
                        task_event["taskData"]["createdBy"], users
                    )
                prev_stage = task_event["createEvent"]["currentStageName"]
            elif task_event.get("inputEvent"):
                if task_event["inputEvent"].get("priority") is not None:
                    event["priority"] = task_event["inputEvent"]["priority"]
                if task_event["inputEvent"].get("overallConsensusScore") is not None:
                    event_type = TaskEventTypes.CONSENSUS_COMPUTED
                    event["stage"] = prev_stage
                    event["score"] = task_event["inputEvent"]["overallConsensusScore"]
                prev_stage = task_event["inputEvent"]["currentStageName"]
            elif task_event.get("outputEvent"):
                if task_event["outputEvent"].get("timeSpentMs") is not None:
                    event["timeSpentMs"] = task_event["outputEvent"]["timeSpentMs"]
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
                            else (
                                (
                                    TaskEventTypes.TASK_ACCEPTED
                                    if review_result
                                    else TaskEventTypes.TASK_CORRECTED
                                )
                                if task_event["outputEvent"]["outputBool"]
                                else TaskEventTypes.TASK_REJECTED
                            )
                        )
                        event["stage"] = task_event["outputEvent"]["currentStageName"]
                        event["updatedBy"] = user_format(
                            prev_assignee or task_event["taskData"]["createdBy"], users
                        )
                prev_stage = task_event["outputEvent"]["currentStageName"]

            if with_labels and task_event.get("taskData"):
                task_data = task_event["taskData"]
                updated_by = user_format(task_data.get("createdByEntity"))

                updated_at = task_data["createdAt"]
                if task_data.get("labelsDataPath"):
                    labels = None
                    labels_data_path = task_data["labelsDataPath"]
                else:
                    labels = [
                        clean_rb_label(label)
                        for label in json.loads(task_data.get("labelsData") or "[]")
                    ]
                    labels_data_path = None
                label_storage_id = task_data["labelsStorage"]["storageId"]
                labels_map = task_data.get("labelsMap", []) or []
                task_datapoint_attributes: Optional[List[Dict]] = task["datapoint"].get(
                    "attributes"
                )
                event["labels"] = flat_rb_format(
                    labels,
                    labels_data_path,
                    task["datapoint"]["items"],
                    [],
                    task["datapoint"]["name"],
                    updated_by,
                    updated_at,
                    updated_by,
                    updated_at,
                    task["taskId"],
                    task["currentStageName"],
                    task["priority"],
                    labels_map,
                    task["datapoint"].get("seriesInfo"),
                    task["datapoint"].get("metaData"),
                    task["datapoint"]["storageMethod"]["storageId"],
                    label_storage_id,
                    {},
                    None,
                    None,
                    None,
                    task_datapoint_attributes,
                )

        elif task_event["__typename"] == "Comment":
            event_type = TaskEventTypes.COMMENT_ADDED
            event.update(comment_format(task_event, users))
            event["replies"] = [
                comment_format(reply, users) for reply in task_event["replies"]
            ]
            prev_stage = event["stage"]
        elif task_event["__typename"] == "TaskStateChanges":
            if task_event["reviewResultBefore"] != task_event["reviewResultAfter"]:
                review_result = task_event["reviewResultAfter"]
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

            elif (task_event.get("assignedToBeforeEntity") or {}).get("userId") != (
                task_event.get("assignedToAfterEntity") or {}
            ).get("userId"):
                if not task_event.get("assignedToAfterEntity"):
                    event_type = TaskEventTypes.TASK_UNASSIGNED
                    event["prevAssignee"] = user_format(
                        task_event["assignedToBeforeEntity"], users
                    )
                elif task_event.get("assignedToBeforeEntity"):
                    event_type = TaskEventTypes.TASK_REASSIGNED
                    event["assignee"] = user_format(
                        task_event["assignedToAfterEntity"], users
                    )
                    event["prevAssignee"] = user_format(
                        task_event["assignedToBeforeEntity"], users
                    )
                else:
                    event_type = TaskEventTypes.TASK_ASSIGNED
                    event["assignee"] = user_format(
                        task_event["assignedToAfterEntity"], users
                    )

            elif task_event["statusBefore"] != task_event["statusAfter"]:
                if task_event["statusAfter"] == "SKIPPED":
                    event_type = TaskEventTypes.TASK_SKIPPED
                    event["assignee"] = user_format(
                        task_event.get("assignedToAfterEntity"), users
                    )
                elif task_event["statusAfter"] == "IN_PROGRESS" and task_event[
                    "statusBefore"
                ] in ("SKIPPED", "ASSIGNED"):
                    event_type = TaskEventTypes.TASK_SAVED
                    event["assignee"] = user_format(
                        task_event.get("assignedToAfterEntity"), users
                    )
                    if type_pos.get(TaskEventTypes.TASK_SAVED, -1) >= 0:
                        events.pop(type_pos[TaskEventTypes.TASK_SAVED])
                        last_pos -= 1

            event["stage"] = task_event["stageNameAfter"] or prev_stage

            if task_event["stageNameAfter"]:
                prev_stage = task_event["stageNameAfter"]

            prev_assignee = task_event["assignedToAfterEntity"]

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
