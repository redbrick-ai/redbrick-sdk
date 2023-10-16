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
  priority?: number;
  createdBy?: string;
  createdAt?: string;
  updatedBy?: string;
  updatedAt?: string;
  metaData?: {[key: string]: string};
};

// A single series can be 2D, 3D, video etc.
type Series = {
  items: string | string[];
  name?: string;
  metaData?: {[key: string]: string};
  segmentations?: string | string[];
  segmentMap?: {
    [instanceId: string]: number | string | string[] | {
      category: number | string | string[];
      attributes?: Attributes;
    };
  };
  binaryMask?: boolean;
  semanticMask?: boolean;
  pngMask?: boolean;
  landmarks?: Landmarks[];
  landmarks3d?: Landmarks3D[];
  measurements?: (MeasureLength | MeasureAngle)[];
  ellipses?: Ellipse[];
  boundingBoxes?: BoundingBox[];
  cuboids?: Cuboid[];
  polygons?: Polygon[];
  polylines?: Polyline[];
  classifications?: Classification[];
  instanceClassifications?: InstanceClassification[];
};

// Label Types
type Landmarks = {
  point: Point2D;
  category: number | string | string[];
  attributes?: Attributes;

  // video meta-data
  video?: VideoMetaData;
};

type Landmarks3D = {
  point: VoxelPoint;
  category: number | string | string[];
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
  category: number | string | string[];
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
  category: number | string | string[];
  attributes?: Attributes;
};

type Ellipse = {
  pointCenter: Point2D;
  xRadiusNorm: number;
  yRadiusNorm: number;
  rotationRad: number;
  category: number | string | string[];
  attributes?: Attributes;
  stats?: MeasurementStats;
  // video meta-data
  video?: VideoMetaData;
}

type BoundingBox = {
  pointTopLeft: Point2D;
  wNorm: number;
  hNorm: number;
  category: number | string | string[];
  attributes?: Attributes;
  stats?: MeasurementStats;
  // video meta-data
  video?: VideoMetaData;
};

type Cuboid = {
  point1: VoxelPoint;
  point2: VoxelPoint;
  absolutePoint1: WorldPoint;
  absolutePoint2: WorldPoint;
  category: number | string | string[];
  attributes?: Attributes;
  stats?: MeasurementStats;
}

type Polygon = {
  points: Point2D[];

  category: number | string | string[];
  attributes?: Attributes;
  stats?: MeasurementStats;
  // video meta-data
  video?: VideoMetaData;
};

type Polyline = {
  points: Point2D[];
  category: number | string | string[];
  attributes?: Attributes;

  // video meta-data
  video?: VideoMetaData;
};

type Classification = {
  category?: number | string | string[];
  attributes?: Attributes;
  // video meta-data
  video?: VideoMetaData;
};

type InstanceClassification = {
  fileIndex: number;
  fileName?: string;
  values: {[attributeName: string]: boolean};
}

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

type MeasurementStats = {
  average: number;
  area?: number;
  volume?: number;
  minimum: number;
  maximum: number;
}
