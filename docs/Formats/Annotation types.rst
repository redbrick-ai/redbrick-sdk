
.. _labeling_type_target:

Annotation type definitions
-----------------------------
This section covers definitions of all the annotation object types. The objects are the same for importing annotations, and exporting annotations.

.. list-table:: Annotation type support
   :widths: 50 50 50 50 
   :header-rows: 1

   * - **Annotation type**
     - Video
     - 3D volume
     - 2D image
   * - :attr:`redbrick.types.task.Ellipse`
     - ⨯
     - ☑️
     - ☑️
   * - :attr:`redbrick.types.task.BoundingBox`
     - ☑️
     - ☑️
     - ☑️
   * - :attr:`redbrick.types.task.MeasureLength`
     - ⨯
     - ☑️
     - ☑️
   * - :attr:`redbrick.types.task.MeasureAngle`
     - ⨯
     - ☑️
     - ☑️
   * - :attr:`redbrick.types.task.Cuboid`
     - ⨯
     - ☑️
     - ⨯
   * - :attr:`redbrick.types.task.Polygon`
     - ☑️
     - ⨯
     - ☑️
   * - :attr:`redbrick.types.task.Polyline`
     - ☑️
     - ⨯
     - ☑️


.. automodule:: redbrick.types.task
   :members: Landmarks, Attributes, Landmarks3D, MeasureLength, MeasureAngle, Ellipse, BoundingBox, Cuboid, Polygon, Polyline, Classification, InstanceClassification, CommonLabelProps, VideoMetaData, MeasurementStats, WorldPoint, VoxelPoint, Point2D
   :undoc-members:

