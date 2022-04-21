RedBrick AI SDK
========================================

RedBrick
----------------------
.. automodule:: redbrick
   :members: get_project, get_org, LabelType, StorageMethod
   :show-inheritance:

Project
----------------------
.. automodule:: redbrick.project
   :members:
   :show-inheritance:
   :exclude-members: learning, learning2

Organization
----------------------
.. automodule:: redbrick.organization
   :members:
   :show-inheritance:

Export
----------------------
.. autoclass:: redbrick.export.Export
   :members: redbrick_format, redbrick_png, coco_format, redbrick_nifti, search_tasks
   :show-inheritance:

Upload
----------------------
.. autoclass:: redbrick.upload.Upload
   :members: create_datapoints, create_datapoint_from_masks
   :show-inheritance:

Labeling
----------------------
.. autoclass:: redbrick.labeling.Labeling
   :members: get_tasks, put_tasks, get_task_queue, assign_task, move_tasks_to_start
   :show-inheritance:
