Annotation type definitions
-----------------------------
This section covers definitions of all the annotation object types. The objects are the same for importing annotations, and exporting annotations.

.. list-table:: Annotation type support
   :widths: 50 30 30 30
   :header-rows: 1
   :stub-columns: 1
   :align: center

   * - **Annotation type**
     - Video
     - 3D volume
     - 2D image
   * - :attr:`redbrick.types.task.Ellipse`
     - :material-regular:`disabled_by_default;1.5rem;sd-text-danger`
     - :material-regular:`check_box;1.5rem;sd-text-success`
     - :material-regular:`check_box;1.5rem;sd-text-success`
   * - :attr:`redbrick.types.task.BoundingBox`
     - :material-regular:`check_box;1.5rem;sd-text-success`
     - :material-regular:`check_box;1.5rem;sd-text-success`
     - :material-regular:`check_box;1.5rem;sd-text-success`
   * - :attr:`redbrick.types.task.MeasureLength`
     - :material-regular:`disabled_by_default;1.5rem;sd-text-danger`
     - :material-regular:`check_box;1.5rem;sd-text-success`
     - :material-regular:`check_box;1.5rem;sd-text-success`
   * - :attr:`redbrick.types.task.MeasureAngle`
     - :material-regular:`disabled_by_default;1.5rem;sd-text-danger`
     - :material-regular:`check_box;1.5rem;sd-text-success`
     - :material-regular:`check_box;1.5rem;sd-text-success`
   * - :attr:`redbrick.types.task.Cuboid`
     - :material-regular:`disabled_by_default;1.5rem;sd-text-danger`
     - :material-regular:`check_box;1.5rem;sd-text-success`
     - :material-regular:`disabled_by_default;1.5rem;sd-text-danger`
   * - :attr:`redbrick.types.task.Polygon`
     - :material-regular:`check_box;1.5rem;sd-text-success`
     - :material-regular:`disabled_by_default;1.5rem;sd-text-danger`
     - :material-regular:`check_box;1.5rem;sd-text-success`
   * - :attr:`redbrick.types.task.Polyline`
     - :material-regular:`check_box;1.5rem;sd-text-success`
     - :material-regular:`disabled_by_default;1.5rem;sd-text-danger`
     - :material-regular:`check_box;1.5rem;sd-text-success`


.. automodule:: redbrick.types.task
   :members: Landmarks, Attributes, Landmarks3D, MeasureLength, MeasureAngle, Ellipse, BoundingBox, Cuboid, Polygon, Polyline, Classification, InstanceClassification, CommonLabelProps, VideoMetaData, MeasurementStats, WorldPoint, VoxelPoint, Point2D
   :undoc-members:
