Formats
==============================

Import & export formats
------------------------
This section will document the structure used for importing and exporting data from RedBrick AI. For importing & exporting annotations please refer to the :ref:`labeling_type_target`.

Import format
~~~~~~~~~~~~~~~~~~~~~~~~~
The RedBrick AI SDK uses a list of :class:`redbrick.types.task.InputTask` objects for importing data. To import data through the CLI or SDK, create a JSON file that follows the same format.

.. autoclass:: redbrick.types.task.InputTask
   :members:

.. autoclass:: redbrick.types.task.Series
   :members:

   .. autoattribute:: items


Export format
~~~~~~~~~~~~~~~~~~~~~~~~~
The RedBrick SDK will export a list of OutputTasks in an object, along with NIfTI segmentation files if they exist, written to the disk. The CLI will export in the same format in a JSON file.

.. autoclass:: redbrick.types.task.OutputTask
   :members:

.. autoclass:: redbrick.types.task.ConsensusScore
   :members:

.. autoclass:: redbrick.common.enums.TaskStates
   :members:

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


Taxonomy format
----------------------
.. automodule:: redbrick.types.taxonomy
   :members:
   :undoc-members:
