"""Partial queries to prevent duplication."""

ORG_INVITE_SHARD = """
email
role
state
idProvider
"""

ORG_MEMBER_SHARD = """
user {
    userId
    email
    givenName
    familyName
    mfaSetup
    lastSeen
    updatedAt
    idProvider
}
role
tags
active
lastSeen
"""


STORAGE_METHOD_SHARD = """
orgId
storageId
name
provider
details {
    ... on S3BucketStorageDetails {
        bucket
        region
        duration
        access
        roleArn
        endpoint
        accelerate
    }
    ... on GCSBucketStorageDetails {
        bucket
    }
}
createdBy {
    userId
}
createdAt
deleted
"""

ATTRIBUTE_SHARD = """
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
"""

WORKSPACE_SHARD = f"""
orgId
workspaceId
name
desc
createdAt
status
metadataSchema {{
    uniqueName
    displayName
    dataType
    options
    required
}}
classificationSchema {{
    {ATTRIBUTE_SHARD}
}}
cohorts {{
    name
    color
    createdBy
    createdAt
}}
"""

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

OLD_ATTRIBUTE_SHARD = """
name
attrType
whitelist
disabled
"""

OLD_CATEGORY_SHARD = """
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
"""

TAXONOMY_SHARD = f"""
orgId
name
version
createdAt
categories {{
    {OLD_CATEGORY_SHARD}
}}
attributes {{
    {OLD_ATTRIBUTE_SHARD}
}}
taskCategories {{
    {OLD_CATEGORY_SHARD}
}}
taskAttributes {{
    {OLD_ATTRIBUTE_SHARD}
}}
colorMap {{
    name
    color
    classid
    trail
    taskcategory
}}
archived
isNew
taxId
studyClassify {{
    {ATTRIBUTE_SHARD}
}}
seriesClassify {{
    {ATTRIBUTE_SHARD}
}}
instanceClassify {{
    {ATTRIBUTE_SHARD}
}}
objectTypes {{
    category
    classId
    labelType
    attributes {{
        {ATTRIBUTE_SHARD}
    }}
    color
    archived
    parents
    hint
}}
"""

TASK_DATA_SHARD = """
    createdAt
    createdByEmail
    labelsData(interpolate: true)
    labelsDataPath(presigned: false)
    labelsStorage {
        storageId
    }
    labelsMap(presigned: false) {
        seriesIndex
        imageIndex
        labelName
    }
"""

NORMAL_TASK_SHARD = """
    ... on LabelingTask {
        state
        assignedTo {
            userId
            email
        }
    }
"""

CONSENSUS_TASK_SHARD = f"""
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
        dpId
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
        heatMaps {{
            seriesIndex
            seriesName
            name
            item
            preset
            dataRange
            opacityPoints
            opacityPoints3d
            rgbPoints
        }}
        transforms {{
            seriesIndex
            transform
        }}
        centerline {{
            seriesIndex
            name
            centerline
        }}
        storageMethod {{
            storageId
        }}
        attributes
        archived
        cohorts {{
            name
        }}
    """


def task_shard(presigned_items: bool, with_consensus: bool) -> str:
    """Return the task shard for the router query."""
    return f"""
        taskId
        dpId
        currentStageName
        priority
        {f"currentStageSubTask(consensus: true) {{ {CONSENSUS_TASK_SHARD} }}" if with_consensus else f"currentStageSubTask {{ {NORMAL_TASK_SHARD} }}"}
        datapoint {{
            {datapoint_shard(True, presigned_items)}
        }}
        latestTaskData {{
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
                reviewResultBefore
                reviewResultAfter
            }}
        }}
    """
