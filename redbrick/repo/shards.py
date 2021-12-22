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
            }
        }
    }
}
"""
