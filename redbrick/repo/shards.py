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

DATAPOINT_SHARD: str = """
    dataPoint {{
        name
        items(presigned: false)
        {}
        createdAt
        createdByEntity {{
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
    }}
"""


def router_task_shard(presign_items: bool, with_consensus: bool) -> str:
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
            {DATAPOINT_SHARD.format(
                "itemsPresigned:items(presigned: true)" if presign_items else ""
            )}
            {TASK_DATA_SHARD}
        }}
    """
