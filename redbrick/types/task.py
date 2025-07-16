# noqa
""""""

from typing import List, Dict, Literal, Union, TypedDict
from typing_extensions import Required, NotRequired  # type: ignore

from redbrick.common.enums import TaskStates


class Point2D(TypedDict):
    """
    2D pixel point.

    The Point2D coordinates are normalized in relation to the dimensions of the image, meaning they are scaled down to a range between 0 and 1. To convert these normalized points back to their original scale on the image, you "un-normalize" them by multiplying by the image's dimensions. This operation typically results in a floating-point number.

    RedBrick AI enhances the precision of annotations on its canvas by **supporting a resolution higher than that of the underlying image**. This capability facilitates sub-pixel annotation accuracy. However, if sub-pixel precision is not necessary for your application, you can simplify the process **by rounding the un-normalized coordinates to the nearest whole number**. This adjustment converts the precise floating-point values back to standard pixel coordinates, making them easier to work with for general purposes.

    .. important::

        The origin point (0,0) from which these coordinates are measured is at the top left of the image. However, for mammography and DBT the origin is the top right of the image.

    """

    #: X co-ordinate normalized by the width of the image.
    xNorm: float

    #: Y co-ordinate normalized by the height of the image.
    yNorm: float


class VoxelPoint(TypedDict):
    """Represents a three-dimensional point in image-space, where i, j, and k  are columns, rows, and k is the slice number."""

    i: int
    j: int
    k: int


class WorldPoint(TypedDict):
    """Represents a three-dimensional point in physical space/world co-ordinates. The world co-ordinates are calculated using :attr:`redbrick.types.task.VoxelPoint` and the DICOM Image Plane Module."""

    x: float
    y: float
    z: float


class MeasurementStats(TypedDict):
    """Measurement statistics for annotations."""

    #: Average pixel/voxel intensity within the annotation. In CT, this is the average HU value.
    average: float

    #: Area contained within the annotation in mm^2.
    area: NotRequired[float]

    #: Volume contained within the annotation in mm^3
    volume: NotRequired[float]

    #: Minimum intensity value within the annotation.
    minimum: float

    #: Maximum intensity value within the annotation.
    maximum: float


class VideoMetaData(TypedDict):
    """
    Contains annotation information along the third axis. Frames for video, and slices for 3D volumes.

    .. warning:: :attr:`redbrick.types.task.VideoMetaData` has a misleading name. It contains information for both videos, and 3D volumes.

    .. hint:: Watch `this video <https://share.redbrickai.com/vpKDGyBd>`_ for a detailed explaination of all the attributes of this object.

    """

    #: The index of the file in series "items" list that this annotation is present on.
    seriesItemIndex: NotRequired[int]

    #: Frame index of the annotation for nifti and dicom multipart files.
    seriesFrameIndex: NotRequired[int]

    #: The frame number (for video) or slice index (for 3D volumes) the annotation is present on.
    frameIndex: NotRequired[int]

    #: Each distinct object has a unique trackId. Two annotations on different frameIndex's with the same trackId's represent the same distinct object.
    trackId: NotRequired[str]

    #: If True, this annotation is user-defined. If False, this annotation is interpolated.
    keyFrame: NotRequired[bool]

    #: If True, this annotation is the last annotation of a specific track defined by trackId.
    endTrack: NotRequired[bool]


Category = Union[int, str, List[str]]


#: Attributes for Taxonomy objects.
#: Attributes can be boolean, textfields, select's or multi-select's.
Attributes = Dict[str, Union[str, bool, List[str]]]


class CommentPin(TypedDict):
    """Comment pin."""

    pointX: float
    pointY: float
    pointZ: float
    frameIndex: NotRequired[int]
    volumeIndex: NotRequired[int]


class CommentType(TypedDict):
    """Comment type."""

    text: str
    pin: NotRequired[CommentPin]


Comment = Union[str, CommentType]


class CommonLabelProps(TypedDict, total=False):
    """Full version of :attr:`redbrick.types.task.Series.segmentMap`."""

    #: Label ID.
    id: NotRequired[str]

    #: Taxonomy object category.
    category: Category

    #: Associated taxonomy object attributes.
    attributes: Attributes

    #: Filepath to segmentation file for this annotation.
    mask: Union[str, List[str]]

    #: Overlapping instances that this label is part of (when without_masks is set).
    overlappingGroups: List[int]

    #: Linked label group id.
    group: str

    #: Read only status
    readOnly: NotRequired[bool]

    #: Comment to add for the label entity
    comment: NotRequired[Comment]


SegmentMap = Dict[Union[str, int], Union[str, int, List[str], CommonLabelProps]]


class InstanceClassification(TypedDict):
    """Instance level classifications for frame-by-frame (video) or slice-by-slice (volume) classifications.."""

    #: Label ID.
    id: NotRequired[str]

    #: For video this is the frameIndex, for DICOM volumes this is the sliceIndex.
    fileIndex: int

    #: The file name represented by frameIndex.
    fileName: NotRequired[str]

    #: Classification value for this frame.
    values: Attributes

    #: Linked label group id.
    group: NotRequired[str]

    #: Read only status
    readOnly: NotRequired[bool]

    #: Comment to add for the label entity
    comment: NotRequired[Comment]


class Classification(TypedDict):
    """Study or series classification."""

    #: Label ID.
    id: NotRequired[str]

    #: Classification attributes.
    attributes: NotRequired[Attributes]

    #: Linked label group id.
    group: NotRequired[str]

    #: Read only status
    readOnly: NotRequired[bool]

    #: Comment to add for the label entity
    comment: NotRequired[Comment]


class Polyline(TypedDict):
    """Open polylines, not supported in 3D images."""

    #: Label ID.
    id: NotRequired[str]

    points: List[Point2D]
    category: Category
    attributes: NotRequired[Attributes]
    video: NotRequired[VideoMetaData]

    #: Linked label group id.
    group: NotRequired[str]

    #: Read only status
    readOnly: NotRequired[bool]

    #: Comment to add for the label entity
    comment: NotRequired[Comment]


class Polygon(TypedDict):
    """Closed polygons, not supported in 3D images."""

    #: Label ID.
    id: NotRequired[str]

    points: List[Point2D]
    category: Category
    attributes: NotRequired[Attributes]
    stats: NotRequired[MeasurementStats]
    video: NotRequired[VideoMetaData]

    #: Linked label group id.
    group: NotRequired[str]

    #: Read only status
    readOnly: NotRequired[bool]

    #: Comment to add for the label entity
    comment: NotRequired[Comment]


class Cuboid(TypedDict):
    """3D bounding boxes for 3D images."""

    #: Label ID.
    id: NotRequired[str]

    #: Top left diagonal corner.
    point1: VoxelPoint

    #: Bottom right diagonal corner.
    point2: VoxelPoint
    absolutePoint1: NotRequired[WorldPoint]
    absolutePoint2: NotRequired[WorldPoint]
    category: Category
    attributes: NotRequired[Attributes]
    stats: NotRequired[MeasurementStats]

    #: Linked label group id.
    group: NotRequired[str]

    #: Read only status
    readOnly: NotRequired[bool]

    #: Comment to add for the label entity
    comment: NotRequired[Comment]


class BoundingBox(TypedDict):
    """
    2D bounding box for 2D images, or slice by slice annotation in 3D images.

    .. hint:: See the `following diagram <https://share.redbrickai.com/T0jPZFn9>`_ to understand the coordinate system.

    """

    #: Label ID.
    id: NotRequired[str]

    #: Coordinates of the top left of the bounding box.
    pointTopLeft: Point2D

    #: Width of the bounding box, normalized by image width.
    wNorm: float

    #: Height of the bounding box, normalized by the image height.
    hNorm: float

    category: Category
    attributes: NotRequired[Attributes]
    stats: NotRequired[MeasurementStats]
    video: NotRequired[VideoMetaData]

    #: Linked label group id.
    group: NotRequired[str]

    #: Read only status
    readOnly: NotRequired[bool]

    #: Comment to add for the label entity
    comment: NotRequired[Comment]


class Ellipse(TypedDict):
    """
    Ellipse annotation.

    .. hint:: See `this ellipse diagram <https://share.redbrickai.com/6PH9ypkl>`_ to understand the coordinate system. Please read the :attr:`redbrick.types.task.Point2D` documentation to understand how normalization works & the origin of the coordinate system.

    .. warning:: For DICOM images of a certain type, ellipse annotations might be flipped i.e., rotating the ellipse clockwise would result in counter-clockwise rotation.
        If you encounter these cases, reach out to our support for instructions on how to handle this support@redbrickai.com.
    """

    #: Label ID.
    id: NotRequired[str]

    #: The normalized center of the ellipse.
    pointCenter: Point2D

    #: The x axis of the ellipse, normalized with by the image width. Adjusting for `rotationRad`, the x-axis of the ellipse aligns with the x-axis of the image.
    xRadiusNorm: float

    #: The y axis of the ellipse, normalized with by the image width. Adjusting for `rotationRad`, the y-axis of the ellipse aligns with the y-axis of the image.
    yRadiusNorm: float

    #: The rotation of the ellipse measured clockwise as the angle between the y-axis of the ellipse and y-axis of the image.
    rotationRad: float
    category: Category
    attributes: NotRequired[Attributes]
    stats: NotRequired[MeasurementStats]
    video: NotRequired[VideoMetaData]

    #: Linked label group id.
    group: NotRequired[str]

    #: Read only status
    readOnly: NotRequired[bool]

    #: Comment to add for the label entity
    comment: NotRequired[Comment]


class MeasureAngle(TypedDict):
    """
    Angle measurement label.

    An angle measurement is defined by three points, where `vertex` is the middle point between `point1` and `point2`. The angle between the two vectors (point1, vertex) and (point2, vertex) defines the angle measurement.

    .. hint:: See `this angle diagram <https://share.redbrickai.com/rqW3sZtf>`_ to understand the coordinate system.
    """

    #: Label ID.
    id: NotRequired[str]

    type: Literal["angle"]
    point1: VoxelPoint
    vertex: VoxelPoint
    point2: VoxelPoint
    absolutePoint1: NotRequired[WorldPoint]
    absoluteVertex: NotRequired[WorldPoint]
    absolutePoint2: NotRequired[WorldPoint]
    normal: List[float]
    """
    Measurements can be made on oblique planes. `normal` defines the normal unit vector to the slice on which the annotation was made. For annotations made on non-oblique planes, the normal will be [0,0,1].
    The measurement is fully defined even without `normal`, however, for completeness `see this angle diagram <https://share.redbrickai.com/CZ5BXXWK>`_ for it's definition.
    """

    #: Measurement angle in degrees.
    angle: NotRequired[float]
    category: Category
    attributes: NotRequired[Attributes]

    #: Linked label group id.
    group: NotRequired[str]

    #: Read only status
    readOnly: NotRequired[bool]

    #: Comment to add for the label entity
    comment: NotRequired[Comment]


class MeasureLength(TypedDict):
    """
    Length measurement label.

    A length measurement is defined by two points, and the length measurement is the distance between the two points.
    """

    #: Label ID.
    id: NotRequired[str]

    type: Literal["length"]
    point1: VoxelPoint
    point2: VoxelPoint
    absolutePoint1: NotRequired[WorldPoint]
    absolutePoint2: NotRequired[WorldPoint]
    normal: List[float]
    """
    Measurements can be made on oblique planes. `normal` defines the normal unit vector to the slice on which the annotation was made. For annotations made on non-oblique planes, the normal will be [0,0,1].
    The measurement is fully defined even without `normal`, however, for completeness `see this length diagram <https://share.redbrickai.com/CZ5BXXWK>`_ for it's definition.
    """

    #: The value of the measurement in millimeters.
    length: NotRequired[float]
    category: Category
    attributes: NotRequired[Attributes]

    #: Linked label group id.
    group: NotRequired[str]

    #: Read only status
    readOnly: NotRequired[bool]

    #: Comment to add for the label entity
    comment: NotRequired[Comment]


class Landmark3D(TypedDict):
    """3D landmark for 3D data."""

    #: Label ID.
    id: NotRequired[str]

    point: VoxelPoint
    category: Category
    attributes: NotRequired[Attributes]

    #: Linked label group id.
    group: NotRequired[str]

    #: Read only status
    readOnly: NotRequired[bool]

    #: Comment to add for the label entity
    comment: NotRequired[Comment]


class Landmark(TypedDict):
    """2D landmark for 2D data."""

    #: Label ID.
    id: NotRequired[str]

    point: Point2D
    category: Category
    attributes: NotRequired[Attributes]
    video: NotRequired[VideoMetaData]

    #: Linked label group id.
    group: NotRequired[str]

    #: Read only status
    readOnly: NotRequired[bool]

    #: Comment to add for the label entity
    comment: NotRequired[Comment]


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


class HeatMap(TypedDict, total=False):
    """Heat map."""

    #: Name.
    name: str

    #: File path.
    item: Required[str]

    #: Preset.
    preset: str

    #: Data range.
    dataRange: List[float]

    #: Opacity points.
    opacityPoints: List[float]

    #: Opacity points 3D.
    opacityPoints3d: List[float]

    #: RGB points.
    rgbPoints: List[float]


class Transform(TypedDict):
    """Transform."""

    #: Transformation matrix (4x4).
    transform: List[List[float]]


class Centerline(TypedDict):
    """Centerline info."""

    #: Centerline name
    name: str

    #: Centerline polydata
    centerline: Dict


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
                "2": {
                    "category": "category b",
                    "mask": "path/to/segmentation.nii"
                    "attributes": Attributes
                }
            }
    """

    #: Heatmaps for the series.
    heatMaps: List[HeatMap]

    #: Transforms for the series.
    transforms: List[Transform]

    #: Centerline info for the series.
    centerline: List[Centerline]

    #: Treats all files in :attr:`redbrick.types.task.Series.segmentations` as binary masks. That is, any non-zero value will be treated as a single instance.
    binaryMask: bool

    semanticMask: bool

    #: Set to true if uploading PNG masks.
    pngMask: bool

    #: 2D landmarks for 2D data.
    landmarks: List[Landmark]

    #: 3D landmarks for 3D data.
    landmarks3d: List[Landmark3D]

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

    #: Current status of the task in the workflow.
    status: TaskStates

    #: E-mail of the user who uploaded this task.
    createdBy: str

    #: Timestamp of when this task was uploaded.
    createdAt: str

    #: Storage method where the task items are hosted.
    storageId: str

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

    #: Datapoint classification attributes.
    datapointClassification: Classification
