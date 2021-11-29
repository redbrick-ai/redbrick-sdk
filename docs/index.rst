RedBrick AI Python SDK Documentation
========================================

.. toctree::
   :maxdepth: 3
   :caption: Contents:

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
   :members: redbrick_format, redbrick_png, coco_format
   :show-inheritance:

Upload
----------------------
.. autoclass:: redbrick.upload.Upload
   :members: create_datapoints, create_datapoint_from_masks
   :show-inheritance:

Labeling
----------------------
.. autoclass:: redbrick.labeling.Labeling
   :members: get_tasks, put_tasks
   :show-inheritance: