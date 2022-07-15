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
"""

TASK_SHARD = """
    taskId
    dpId
    currentStageName
    latestTaskData {{
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
            }}
            storageMethod {{
                storageId
            }}
        }}
        createdAt
        createdByEmail
        labelsData(interpolate: true)
        labelsStorage {{
            storageId
        }}
        labelsMap(presigned: false) {{
            labelName
            imageIndex
            imageName
            seriesId
        }}
    }}
"""
