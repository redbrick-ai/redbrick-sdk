"""Partial queries to prevent duplication."""

PROJECT_SHARD = """
orgId
projectId
name
desc
status
tdType
taxonomy {
    name
}
projectUrl
createdAt
consensusSettings {
    enabled
}
workspace {
    workspaceId
}
"""

STAGE_SHARD = """
stageName
brickName
stageConfig
routing {
    ...on NoRouting {
        placeholder
    }
    ...on NextRouting {
        nextStageName
    }
    ...on MultiRouting {
        stageNames
    }
    ...on BooleanRouting {
        passed
        failed
    }
    ...on FeedbackRouting {
        feedbackStageName
    }
}
"""

TAXONOMY_SHARD = """
orgId
name
version
createdAt
categories {
    name
    children {
        name
        classId
        disabled
        children {
            name
            classId
            disabled
            children {
                name
                classId
                disabled
                children {
                    name
                    classId
                    disabled
                    children {
                        name
                        classId
                        disabled
                        children {
                            name
                            classId
                            disabled
                        }
                    }
                }
            }
        }
    }
}
attributes {
    name
    attrType
    whitelist
    disabled
}
taskCategories {
    name
    children {
        name
        classId
        disabled
        children {
            name
            classId
            disabled
            children {
                name
                classId
                disabled
                children {
                    name
                    classId
                    disabled
                    children {
                        name
                        classId
                        disabled
                        children {
                            name
                            classId
                            disabled
                        }
                    }
                }
            }
        }
    }
}
taskAttributes {
    name
    attrType
    whitelist
    disabled
}
colorMap {
    name
    color
    classid
    trail
    taskcategory
}
archived
isNew
taxId
studyClassify {
    name
    attrType
    attrId
    options {
        name
        optionId
        color
        archived
    }
    archived
    parents
    hint
    defaultValue
}
seriesClassify {
    name
    attrType
    attrId
    options {
        name
        optionId
        color
        archived
    }
    archived
    parents
    hint
    defaultValue
}
instanceClassify {
    name
    attrType
    attrId
    options {
        name
        optionId
        color
        archived
    }
    archived
    parents
    hint
    defaultValue
}
objectTypes {
    category
    classId
    labelType
    attributes {
        name
        attrType
        attrId
        options {
            name
            optionId
            color
            archived
        }
        archived
        parents
        hint
        defaultValue
    }
    color
    archived
    parents
    hint
}
"""

TASK_DATA_SHARD = """
    createdAt
    createdByEmail
    labelsData(interpolate: true)
    labelsStorage {
        storageId
    }
    labelsMap(presigned: false) {
        imageIndex
        labelName
    }
"""

TASK_SHARD = f"""
    ... on LabelingTask {{
        state
        assignedTo {{
            userId
            email
        }}
        taskData {{
            {TASK_DATA_SHARD}
        }}
        subTasks {{
            state
            assignedTo {{
                userId
                email
            }}
            taskData {{
                {TASK_DATA_SHARD}
            }}
        }}
        overallConsensusScore
        consensusInfo {{
            user {{
                userId
                email
            }}
            taskData {{
                {TASK_DATA_SHARD}
            }}
            scores {{
                user {{
                    userId
                    email
                }}
                score
            }}
        }}
    }}
"""


def datapoint_shard(raw_items: bool, presigned_items: bool) -> str:
    """Return the datapoint shard."""
    return f"""
        name
        {"items(presigned: false)" if raw_items else ""}
        {"itemsPresigned:items(presigned: true)" if presigned_items else ""}
        createdAt
        createdByEntity {{
            userId
            email
        }}
        metaData
        seriesInfo {{
            name
            itemsIndices
            dataType
            metaData
        }}
        storageMethod {{
            storageId
        }}
    """


def task_shard(presigned_items: bool, with_consensus: bool) -> str:
    """Return the task shard for the router query."""
    return f"""
        taskId
        dpId
        currentStageName
        priority
        currentStageSubTask{"(consensus: true)" if with_consensus else ""} {{
            {TASK_SHARD}
        }}
        latestTaskData {{
            dataPoint {{
                {datapoint_shard(True, presigned_items)}
            }}
            {TASK_DATA_SHARD}
        }}
    """


def router_task_shard(with_labels: bool) -> str:
    """Return router task shard for events query."""
    return f"""
        taskId
        currentStageName
        datapoint {{
            {datapoint_shard(True, False)}
        }}
        priority
        genericEvents {{
            __typename
            ... on TaskEvent {{
                eventId
                createdAt
                createEvent {{
                    currentStageName
                    isGroundTruth
                    priority
                }}
                inputEvent {{
                    currentStageName
                    overallConsensusScore
                    priority
                }}
                outputEvent {{
                    currentStageName
                    outputBool
                    timeSpentMs
                }}
                taskData {{
                    stageName
                    createdBy
                    {TASK_DATA_SHARD if with_labels else ''}
                }}
            }}
            ... on Comment {{
                commentId
                createdBy {{
                    userId
                }}
                textVal
                createdAt
                stageName
                issueComment
                issueResolved
                replies {{
                    commentId
                    createdBy {{
                        userId
                    }}
                    textVal
                    createdAt
                    stageName
                    issueComment
                    issueResolved
                }}
            }}
            ... on TaskStateChanges {{
                stageNameAfter: stageName
                assignedAtAfter
                createdAt
                statusBefore
                statusAfter
                assignedToBefore
                assignedToAfter
                consensusAssigneesBefore
                consensusAssigneesAfter
                consensusStatusesBefore
                consensusStatusesAfter
            }}
        }}
    """
