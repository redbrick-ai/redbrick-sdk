"""Partial queries to prevent duplication."""

LABEL_SHARD = """
category
attributes {
    name
    value
}
labelid
frameindex
trackid
keyframe
taskclassify
tasklevelclassify
frameclassify
end
bbox2d {
    xnorm
    ynorm
    wnorm
    hnorm
}
point {
    xnorm
    ynorm
}
polyline {
    xnorm
    ynorm
}
polygon {
    xnorm
    ynorm
}
pixel {
    imagesize
    regions
    holes
}
ellipse {
    xcenternorm
    ycenternorm
    xnorm
    ynorm
    rot
}
ocrvalue
"""
