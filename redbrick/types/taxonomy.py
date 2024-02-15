"""Taxonomy types."""

from typing import List, Optional, Union, TypedDict, Literal
from typing_extensions import Required, NotRequired  # type: ignore


AttributeType = Literal[
    "BOOL",
    "TEXT",
    "SELECT",
    "MULTISELECT",
]

LabelType = Literal[
    "BBOX",
    "CUBOID",
    "POINT",
    "POLYLINE",
    "POLYGON",
    "ELLIPSE",
    "SEGMENTATION",
    "LENGTH",
    "ANGLE",
]


class AttributeOption(TypedDict, total=False):
    """Attribute Option."""

    name: Required[str]
    optionId: Required[int]
    color: str
    archived: bool


class Attribute(TypedDict, total=False):
    """Attribute."""

    name: Required[str]
    attrType: Required[AttributeType]
    attrId: Required[int]
    options: Optional[List[AttributeOption]]
    archived: bool
    parents: Optional[List[str]]
    hint: Optional[str]
    defaultValue: Optional[Union[str, bool, int, List[int]]]


class ObjectType(TypedDict, total=False):
    """Object Type."""

    category: Required[str]
    classId: Required[int]
    labelType: Required[LabelType]
    attributes: Optional[List[Attribute]]
    color: str
    archived: bool
    parents: Optional[List[str]]
    hint: Optional[str]


class Taxonomy(TypedDict):
    """Taxonomy."""

    orgId: str  # UUID
    taxId: str  # UUID
    name: str

    studyClassify: List[Attribute]
    seriesClassify: List[Attribute]
    instanceClassify: List[Attribute]
    objectTypes: List[ObjectType]

    createdAt: str  # datetime
    archived: NotRequired[bool]

    isNew: NotRequired[bool]  # not in use
