"""Task types."""

from typing import List, Dict, Literal, Union, TypedDict
from typing_extensions import Required, NotRequired  # type: ignore

from redbrick.common.enums import TaskStates


class Point2D(TypedDict):
    """2D pixel point."""

    #: X co-ordinate normalized by the width of the image.
    xNorm: float

    #: Y co-ordinate normalized by the height of the image.
    yNorm: float


class VoxelPoint(TypedDict):
    """Represents a three-dimensional point in image-space, where i, j, and k are columns, rows, and k is the slice number.."""

    i: int
    j: int
    k: int


class WorldPoint(TypedDict):
    """Represents a three-dimensional point in physical space/world co-ordinates. The world co-ordinates are calculated using :attr:`redbrick.types.task.VoxelPoint` and the DICOM Image Plane Module."""

    x: float
    y: float
    z: float


class MeasurementStats(TypedDict):
    """Label measurement stats."""

    average: float
    area: NotRequired[float]
    volume: NotRequired[float]
    minimum: float
    maximum: float


class VideoMetaData(TypedDict):
    """Frame and tracking information for an annotation on a video."""

    #: The frame number the annotation is present on.
    frameIndex: int

    #: Each distinct object has a unique trackId. Two annotations on different frameIndex's with the same trackId's represent the same distinct object.
    trackId: str

    #: If True, this annotation is user-defined. If False, this annotation is interpolated.
    keyFrame: bool

    #: If True, this annotation is the last annotation of a specific track defined by trackId.
    endTrack: bool


Category = Union[int, str, List[str]]


#: Attributes for Taxonomy objects.
#: Attributes can be boolean, textfields, select's or multi-select's.
Attributes = Dict[str, Union[str, bool, List[str]]]


class CommonLabelProps(TypedDict, total=False):
    """Full version of :attr:`redbrick.types.task.Series.segmentMap`."""

    #: Taxonomy object category.
    category: Category

    #: Associated taxonomy object attributes.
    attributes: Attributes

    #: Filepath to segmentation file for this annotation.
    mask: Union[str, List[str]]


SegmentMap = Dict[Union[str, int], Union[str, int, List[str], CommonLabelProps]]


class InstanceClassification(TypedDict):
    """Instance level classifications for frame-by-frame (video) or slice-by-slice (volume) classifications.."""

    #: For video this is the frameIndex, for DICOM volumes this is the sliceIndex.
    fileIndex: int

    #: The file name represented by frameIndex.
    fileName: NotRequired[str]

    #: Classification value for this frame.
    values: Attributes


class Classification(TypedDict):
    """Study or series classification."""

    attributes: NotRequired[Attributes]


class Polyline(TypedDict):
    """Open polylines, not supported in 3D images."""

    points: List[Point2D]
    category: Category
    attributes: NotRequired[Attributes]

    #: Video track information, if this annotation is on a video.
    video: NotRequired[VideoMetaData]


class Polygon(TypedDict):
    """Closed polygons, not supported in 3D images."""

    points: List[Point2D]
    category: Category
    attributes: NotRequired[Attributes]
    stats: NotRequired[MeasurementStats]

    #: Video track information, if this annotation is on a video.
    video: NotRequired[VideoMetaData]


class Cuboid(TypedDict):
    """3D bounding boxes for 3D images."""

    #: Top left diagonal corner.
    point1: VoxelPoint

    #: Bottom right diagonal corner.
    point2: VoxelPoint
    absolutePoint1: WorldPoint
    absolutePoint2: WorldPoint
    category: Category
    attributes: NotRequired[Attributes]
    stats: NotRequired[MeasurementStats]


class BoundingBox(TypedDict):
    """2D bounding box for 2D images, or slice by slice annotation in 3D images."""

    pointTopLeft: Point2D
    wNorm: float
    hNorm: float
    category: Category
    attributes: NotRequired[Attributes]
    stats: NotRequired[MeasurementStats]
    video: NotRequired[VideoMetaData]


class Ellipse(TypedDict):
    """Ellipse annotation. Not supported in Videos."""

    pointCenter: Point2D
    xRadiusNorm: float
    yRadiusNorm: float
    rotationRad: float
    category: Category
    attributes: NotRequired[Attributes]
    stats: NotRequired[MeasurementStats]
    video: NotRequired[VideoMetaData]


class MeasureAngle(TypedDict):
    """
    Angle measurement label.

    An angle measurement is defined by three points, where `vertex` is the middle point between `point1` and `point2`. The angle between the two vectors <point1, vertex> and <point2, vertex> defines the angle measurement.
    """

    type: Literal["angle"]
    point1: VoxelPoint
    vertex: VoxelPoint
    point2: VoxelPoint
    absolutePoint1: WorldPoint
    absoluteVertex: WorldPoint
    absolutePoint2: WorldPoint

    #: Measurements can be made on oblique planes. `normal` defines the normal unit vector to the slice on which the annotation was made. For annotations made on non-oblique planes, the normal will be [0,0,1].
    normal: List[float]

    #: Measurement angle in degrees.
    angle: float
    category: Category
    attributes: NotRequired[Attributes]


class MeasureLength(TypedDict):
    """
    Length measurement label.

    A length measurement is defined by two points, and the length measurement is the distance between the two points.
    """

    type: Literal["length"]
    point1: VoxelPoint
    point2: VoxelPoint
    absolutePoint1: WorldPoint
    absolutePoint2: WorldPoint

    #: Measurements can be made on oblique planes. `normal` defines the normal unit vector to the slice on which the annotation was made. For annotations made on non-oblique planes, the normal will be [0,0,1].
    normal: List[float]

    #: The value of the measurement in millimeters.
    length: float
    category: Category
    attributes: NotRequired[Attributes]


class Landmarks3D(TypedDict):
    """3D landmarks for 3D data."""

    point: VoxelPoint
    category: Category
    attributes: NotRequired[Attributes]


class Landmarks(TypedDict):
    """2D landmarks for 2D data."""

    point: Point2D
    category: Category
    attributes: NotRequired[Attributes]
    video: NotRequired[VideoMetaData]


class ConsensusScore(TypedDict, total=False):
    """Consensus score for a pair of annotators for a consensus task."""

    #: User who is compared to primary user.
    secondaryUser: str

    #: User id of user who is compared to primary user.
    secondaryUserId: str

    #: User email of user who is compared to the primary user.
    secondaryUserEmail: str

    #: Agreement score between the primary user and this secondary user.
    score: float


class Series(TypedDict, total=False):
    """A single series represents a single volume, image, or video. A :class:`redbrick.types.task.InputTask` can have multiple series."""

    #: Unique identifier for the series that will be displayed on the annotation viewport.
    name: str

    items: Union[str, List[str]]
    """
    Path(s) to the image instances of this series.

    .. tab:: DICOM 3D

        .. code:: python

            # DICOM instances don't need to be in order.
            items = ["instance001.dcm", "instance000.dcm", "instance003.dcm]

    .. tab:: DICOM 2D

        .. code:: python

            items = "path/to/instance.dcm"

    .. tab:: NIfTI

        .. code:: python

            items = "path/to/nifti.nii

    .. tab:: Video frames

        .. code:: python

            # Frames need to be in correct order.
            items = ["fram001.png", "frame002.png", "frame003.png"]
    """

    #: Series level meta-data will be displayed on the viewport.
    metaData: Dict[str, str]

    segmentations: Union[str, List[str]]
    """
    Path to your NIfTI segmentation files for uploading annotations.

    Read our guide on `importing annotation <https://docs.redbrickai.com/python-sdk/importing-annotations-guide>`_ to learn more.

    .. tab:: Single

        If your series has a single segmentation file.

        .. code:: python

            items = "path/to/segmentation.nii"

    .. tab:: Multiple

        If your series has multiple segmentation files for different instances.

        .. code:: python

            items = ["path/to/instance01.nii", "path/to/instance02.nii"]
    """

    segmentMap: SegmentMap
    """
    A mapping between your segmentation file instance values (values inside your NIfTI files) and your RedBrick AI taxonomy categories.

    Read our guide on `importing annotation <https://docs.redbrickai.com/python-sdk/importing-annotations-guide>`_ to learn more.


    .. tab:: Shorthand

        "1" and "2" are values present the NIfTI files defined by :attr:`redbrick.types.task.Series.segmentations`. Those values will be mapped to your RedBrick AI taxonomy categories "category a" and "category b".

        .. code:: Python

            segmentMap = {
                "1": "category a",
                "2": "category b"
            }


    .. tab:: Full

        "1" and "2" are values present the NIfTI files defined by :attr:`redbrick.types.task.Series.segmentations`. Those values will be mapped to your RedBrick AI taxonomy categories "category a" and "category b".

        :code:`Attributes`: :attr:`redbrick.types.task.Attributes`

        .. code:: Python

            segmentMap = {
                "1": {
                    "category": "category a",
                    "mask": "path/to/segmentation.nii"
                    "attributes": Attributes
                },
                "2": "category b"
            }
    """

    #: Treats all files in :attr:`redbrick.types.task.Series.segmentations` as binary masks. That is, any non-zero value will be treated as a single instance.
    binaryMask: bool

    semanticMask: bool

    #: Set to true if uploading PNG masks.
    pngMask: bool

    #: 2D landmarks for 2D data.
    landmarks: List[Landmarks]

    #: 3D landmarks for 3D data.
    landmarks3d: List[Landmarks3D]

    #: Length or angle measurements. Not supported in videos.
    measurements: List[Union[MeasureLength, MeasureAngle]]

    #: Ellipse annotation. Not supported in Videos.
    ellipses: List[Ellipse]

    #: 2D bounding box for 2D images, or slice by slice annotation in 3D images.
    boundingBoxes: List[BoundingBox]

    #: 3D bounding boxes for 3D images.
    cuboids: List[Cuboid]

    #: Closed polygons, not supported in 3D images.
    polygons: List[Polygon]

    #: Open polylines, not supported in 3D images.
    polylines: List[Polyline]

    #: Series level classifications.
    classifications: List[Classification]

    #: Instance level classifications for frame-by-frame (video) or slice-by-slice (volume) classifications.
    instanceClassifications: List[InstanceClassification]


class InputTask(TypedDict, total=False):
    """
    Represents a single task in RedBrick AI, which is a unit of labeling work. This user-defined object
    can contain one or more series of mixed modalities.
    """

    #: A unique user defined string for quickly identifying and searching tasks.
    name: Required[str]

    #: Add more than one series per task by adding multiple entries to `series` list.
    series: Required[List[Series]]

    #: For importing Study level classifications :attr:`redbrick.types.task.Classification`.
    classification: Classification

    #: `priority` must between [0, 1]. Tasks will be ordered in descending order of priority.
    priority: float

    #: Used for displaying Task level meta-data within the annotation viewer.
    metaData: Dict[str, str]

    #: Specify user email(s) to automatically assign this task to them.
    preAssign: Dict[str, Union[str, List[str]]]


class OutputTask(TypedDict, total=False):
    """Single task object on export."""

    #: System generated unique identifier for the task.
    taskId: Required[str]

    #: A unique user defined string for quickly identifying and searching tasks.
    name: Required[str]

    #: List of `series` in the task :attr:`redbrick.types.task.Series`.
    series: Required[List[Series]]

    #: Study level classifications :attr:`redbrick.types.task.Classification`.
    classification: Classification

    #: Task `priority` in the range [0, 1].
    priority: float

    #: Task level meta-data within the annotation viewer.
    metaData: Dict[str, str]

    #: Name of the stage in which this task currently is.
    currentStageName: str

    #: Current status of the task.
    status: TaskStates

    #: E-mail of the user who uploaded this task.
    createdBy: str

    #: Timestamp of when this task was uploaded.
    createdAt: str

    #: E-mail of the user who last edited this task.
    updatedBy: str

    #: System generated unique user ID of user who last edited this task.
    updatedByUserId: str

    #: Timestamp of when this task was last edited.
    updatedAt: str

    #: If true, this task is a consensus task, i.e., it was labeled by more than one person.
    consensus: bool

    consensusScore: float
    """
    Agreement score between annotators who labeled this task.

    Read more about the score calculation `here <https://docs.redbrickai.com/projects/consensus-inter-annotator-agreement/agreement-calculation>`_.
    """

    #: A list of all the results from consensus. One entry for each annotator.
    consensusTasks: List["OutputTask"]

    #: Matrix of the agreement scores between the labelers.
    scores: List[ConsensusScore]

    #: Supertruth version produced in consensus review stage.
    superTruth: "OutputTask"
