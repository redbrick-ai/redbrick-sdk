"""Section covering the formats for all Taxonomy objects. Taxonomies define a labeling schema for your RedBrick AI projects."""

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
    """
    For attrType SELECT and MULTISELECT this defines the list of selection options.
    """

    archived: bool
    parents: Optional[List[str]]
    """
    Defining parents will add a nested structure to the taxonomy.
    Multiple attributes with parent ["Type A"] will be visually nested under a expansion panel Type A in the user interface.

    .. note:: Only supported for Classifications, not for Object Attributes.

    """

    #: A string containing raw text, or HTML. The hints will appear in the viewer.
    hint: Optional[str]

    #: For SELECT or MULTISELECT types, defaultValue will pre-populate the UI with the selection.
    defaultValue: Optional[Union[str, bool, int, List[int]]]


class ObjectType(TypedDict, total=False):
    """Object's are used to annotate features or objects in tasks."""

    #: Category of the Taxonomy object is a string descriptor.
    category: Required[str]

    #: A unique integer for this object. Segmentation files can be exported to contain classId as the values in the file.
    classId: Required[int]

    #: They type of label for this object.
    labelType: Required[LabelType]

    #: Attributes allow further classification of objects.
    attributes: Optional[List[Attribute]]
    color: str
    archived: bool

    #: Defining parents will add a nested structure to the taxonomy.
    #: Multiple objects with parent ["Type A"] will be visually nested under a expansion panel Type A in the user interface.
    parents: Optional[List[str]]

    #: A string containing raw text, or HTML. The hints will appear in the viewer.
    hint: Optional[str]


class Taxonomy(TypedDict):
    """Taxonomy object."""

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
