"""Partial queries to prevent duplication."""

TAXONOMY_SHARD = """
name
version
categories {
    name
    children {
        name
        classId
        children {
            name
            classId
            children {
                name
                classId
                children {
                    name
                    classId
                    children {
                        name
                        classId
                        children {
                            name
                            classId
                        }
                    }
                }
            }
        }
    }
}
"""

LATEST_TASKDATA_SHARD = """
    latestTaskData {
        dataPoint {
            name
            itemsPresigned: items(presigned: true)
            items(presigned: false)
        }
        createdByEmail
        labelsData(interpolate: true)
        labelsPath
    }
"""
