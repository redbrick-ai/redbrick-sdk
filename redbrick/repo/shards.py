"""Partial queries to prevent duplication."""

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
    }
    color
    archived
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

DATAPOINT_SHARD = """
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
            numFrames
            dimensions
        }}
        storageMethod {{
            storageId
        }}
    }}
"""
