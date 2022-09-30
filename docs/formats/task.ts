type Tasks = Task[];

// Single task on RedBrick can be single/multi-series
type Task = {
  // Required on upload and export
  name: string;
  series: Series[];

  // Task level annotation information
  classification?: Classification;

  // Only required on export
  taskId?: string;
  currentStageName?: string;
  createdBy?: string;
  createdAt?: string;
  updatedBy?: string;
  updatedAt?: string;
};

// A single series can be 2D, 3D, video etc.
type Series = {
  items: string | string[];
  name?: string;
  numFrames?: number;
  dimensions?: [number, number, number];
  segmentations?: string | string[];
  segmentMap?: {
    [instanceId: number]: {
      category: string | string[];
      attributes?: Attributes;
    };
  };
  landmarks?: Landmarks[];
  landmarks3d?: Landmarks3D[];
  measurements?: (MeasureLength | MeasureAngle)[];
  boundingBoxes?: BoundingBox[];
  polygons?: Polygon[];
  polylines?: Polyline[];
  classifications?: Classification[];
};

// Label Types
type Landmarks = {
  point: Point2D;
  category: string | string[];
  attributes?: Attributes;

  // video meta-data
  video?: VideoMetaData;
};

type Landmarks3D = {
  point: VoxelPoint;
  category: string | string[];
  attributes?: Attributes;
};

type MeasureLength = {
  type: "length";
  point1: VoxelPoint;
  point2: VoxelPoint;
  absolutePoint1: WorldPoint;
  absolutePoint2: WorldPoint;
  normal: [number, number, number];
  length: number;
  category: string | string[];
  attributes?: Attributes;
};

type MeasureAngle = {
  type: "angle";
  point1: VoxelPoint;
  vertex: VoxelPoint;
  point2: VoxelPoint;
  absolutePoint1: WorldPoint;
  absoluteVertex: WorldPoint;
  absolutePoint2: WorldPoint;
  normal: [number, number, number];
  angle: number;
  category: string | string[];
  attributes?: Attributes;
};

type BoundingBox = {
  pointTopLeft: Point2D;
  wNorm: number;
  hNorm: number;
  category: string | string[];
  attributes?: Attributes;

  // video meta-data
  video?: VideoMetaData;
};

type Polygon = {
  points: Point2D[];

  category: string | string[];
  attributes?: Attributes;

  // video meta-data
  video?: VideoMetaData;
};

type Polyline = {
  points: Point2D[];
  category: string | string[];
  attributes?: Attributes;

  // video meta-data
  video?: VideoMetaData;
};

type Classification = {
  category: string | string[];
  attributes?: Attributes;
  // video meta-data
  video?: VideoMetaData;
};

type Attributes = {
  [attributeName: string]: string | boolean | string[];
};

type VideoMetaData = {
  frameIndex: number;
  trackId: string;
  keyFrame: number;
  endTrack: Boolean;
};

// i is rows, j is columns, k is slice
type VoxelPoint = {
  i: number;
  j: number;
  k: number;
};
// The position of VoxelPoint in physical space (world coordinate) computed using the Image Plane Module
type WorldPoint = {
  x: number;
  y: number;
  z: number;
};
type Point2D = {
  xnorm: number;
  ynorm: number;
};
