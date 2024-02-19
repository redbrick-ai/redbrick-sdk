RedBrick AI SDK
========================================
The SDK is best for writing Python scripts to interact with your RedBrick AI organization & projects. The SDK offers granular
functions for programmatically manipulating data, importing annotations, assigning tasks, and more.

RedBrick
----------------------
.. automodule:: redbrick
   :members: get_org, get_workspace, get_project, StorageMethod, ImportTypes, TaskEventTypes, TaskFilters, Stage, LabelStage, ReviewStage
   :member-order: bysource

Organization
----------------------
.. automodule:: redbrick.organization.RBOrganization
   :members: name, org_id, create_workspace, create_project, create_project_advanced, get_project, taxonomies, projects_raw, projects, labeling_time, create_taxonomy, get_taxonomy, update_taxonomy
   :show-inheritance:

Workspace
----------------------
.. automodule:: redbrick.workspace.RBWorkspace
   :members: name, org_id, workspace_id
   :show-inheritance:

Project
----------------------
.. autoclass:: redbrick.project.RBProject
   :members: name, org_id, project_id, url, taxonomy_name, workspace_id, label_storage, label_stages, review_stages, members, set_label_storage, update_stage
   :show-inheritance:

Export
----------------------
.. autoclass:: redbrick.export.Export
   :members: export_tasks, list_tasks, get_task_events, get_active_time
   :show-inheritance:

Upload
----------------------
.. autoclass:: redbrick.upload.Upload
   :members: create_datapoints, delete_tasks, delete_tasks_by_name, update_task_items, import_tasks_from_workspace, update_tasks_priority
   :show-inheritance:

Labeling
----------------------
.. autoclass:: redbrick.labeling.Labeling
   :members: put_tasks, assign_tasks, move_tasks_to_start
   :show-inheritance:

Settings
----------------------
.. autoclass:: redbrick.settings.Settings
   :members: label_validation, hanging_protocol, toggle_reference_standard_task
   :show-inheritance:

Taxonomy format
----------------------
.. automodule:: redbrick.types.taxonomy
   :members:
   :undoc-members:


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

.. _labeling_type_target:

Annotation type definitions
-----------------------------
This section covers definitions of all the annotation object types. The objects are the same for importing annotations, and exporting annotations.

.. automodule:: redbrick.types.task
   :members: Landmarks, Attributes, Landmarks3D, MeasureLength, MeasureAngle, Ellipse, BoundingBox, Cuboid, Polygon, Polyline, Classification, InstanceClassification, CommonLabelProps, VideoMetaData, MeasurementStats, WorldPoint, VoxelPoint, Point2D 
   :undoc-members:
