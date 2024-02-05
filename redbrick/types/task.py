"""Task types."""

from typing import List, Dict, Union, TypedDict, Required, NotRequired


class Point2D(TypedDict):
    """Point 2D label."""

    xNorm: float
    yNorm: float


class VoxelPoint(TypedDict):
    """Voxel point coordinates."""

    i: int
    j: int
    k: int


class WorldPoint(TypedDict):
    """World point coordinates."""

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
    """Frame and track information for a label."""

    frameIndex: int
    trackId: str
    keyFrame: int
    endTrack: bool


Attributes = Dict[str, Union[str, bool, List[str]]]


class InstanceClassification(TypedDict):
    """Instance classification."""

    fileIndex: int
    fileName: NotRequired[str]
    values: Dict[str, bool]


class Classification(TypedDict):
    """Study or series classification."""

    category: NotRequired[Union[int, str, List[str]]]
    attributes: NotRequired[Attributes]
    video: NotRequired[VideoMetaData]


class Polyline(TypedDict):
    """Polyline label."""

    points: List[Point2D]
    category: Union[int, str, List[str]]
    attributes: NotRequired[Attributes]
    video: NotRequired[VideoMetaData]


class Polygon(TypedDict):
    """Polygon label."""

    points: List[Point2D]
    category: Union[int, str, List[str]]
    attributes: NotRequired[Attributes]
    stats: NotRequired[MeasurementStats]
    video: NotRequired[VideoMetaData]


class Cuboid(TypedDict):
    """Cuboid label."""

    point1: VoxelPoint
    point2: VoxelPoint
    absolutePoint1: WorldPoint
    absolutePoint2: WorldPoint
    category: Union[int, str, List[str]]
    attributes: NotRequired[Attributes]
    stats: NotRequired[MeasurementStats]


class BoundingBox(TypedDict):
    """Bounding box label."""

    pointTopLeft: Point2D
    wNorm: float
    hNorm: float
    category: Union[int, str, List[str]]
    attributes: NotRequired[Attributes]
    stats: NotRequired[MeasurementStats]
    video: NotRequired[VideoMetaData]


class Ellipse(TypedDict):
    """Ellipse label."""

    pointCenter: Point2D
    xRadiusNorm: float
    yRadiusNorm: float
    rotationRad: float
    category: Union[int, str, List[str]]
    attributes: NotRequired[Attributes]
    stats: NotRequired[MeasurementStats]
    video: NotRequired[VideoMetaData]


class MeasureAngle(TypedDict):
    """Angle measurement label."""

    type: str
    point1: VoxelPoint
    vertex: VoxelPoint
    point2: VoxelPoint
    absolutePoint1: WorldPoint
    absoluteVertex: WorldPoint
    absolutePoint2: WorldPoint
    normal: List[float]
    angle: float
    category: Union[int, str, List[str]]
    attributes: NotRequired[Attributes]


class MeasureLength(TypedDict):
    """Length measurement label."""

    type: str
    point1: VoxelPoint
    point2: VoxelPoint
    absolutePoint1: WorldPoint
    absolutePoint2: WorldPoint
    normal: List[float]
    length: float
    category: Union[int, str, List[str]]
    attributes: NotRequired[Attributes]


class Landmarks3D(TypedDict):
    """3D point label."""

    point: VoxelPoint
    category: Union[int, str, List[str]]
    attributes: NotRequired[Attributes]


class Landmarks(TypedDict):
    """2D point label."""

    point: Point2D
    category: Union[int, str, List[str]]
    attributes: NotRequired[Attributes]
    video: NotRequired[VideoMetaData]


class ConsensusScore(TypedDict, total=False):
    """Consensus score (for consensus tasks)."""

    secondaryUser: str
    secondaryUserId: str
    secondaryUserEmail: str
    score: float


class Series(TypedDict, total=False):
    """Task series information."""

    items: Union[str, List[str]]
    name: str
    metaData: Dict[str, str]
    segmentations: Union[str, List[str]]
    segmentMap: Dict[
        Union[str, int],
        Union[str, int, List[str], Dict[str, Union[int, str, List[str]]]],
    ]
    binaryMask: bool
    semanticMask: bool
    pngMask: bool
    landmarks: List[Landmarks]
    landmarks3d: List[Landmarks3D]
    measurements: List[Union[MeasureLength, MeasureAngle]]
    ellipses: List[Ellipse]
    boundingBoxes: List[BoundingBox]
    cuboids: List[Cuboid]
    polygons: List[Polygon]
    polylines: List[Polyline]
    classifications: List[Classification]
    instanceClassifications: List[InstanceClassification]


class Task(TypedDict, total=False):
    """Task object."""

    name: str
    series: Required[List[Series]]
    classification: Classification
    taskId: str
    currentStageName: str
    priority: int
    createdBy: str
    createdAt: str
    updatedBy: str
    updatedAt: str
    metaData: Dict[str, str]
    preAssign: Dict[str, Union[str, List[str]]]
    consensusScore: float
    consensusTasks: List["Task"]
    scores: List[ConsensusScore]
    superTruth: "Task"
