RedBrick AI SDK
========================================
The SDK is best for writing Python scripts to interact with your RedBrick AI organization & projects. The SDK offers granular
functions for programmatically manipulating data, importing annotations, assigning tasks, and more.

RedBrick
----------------------
.. automodule:: redbrick
   :members: get_project, get_org, StorageMethod, ImportTypes
   :show-inheritance:

Project
----------------------
.. autoclass:: redbrick.project.RBProject
   :members: name, org_id, project_id, url, taxonomy_name, label_storage, label_stages, review_stages, members, set_label_storage
   :show-inheritance:

Organization
----------------------
.. automodule:: redbrick.organization
   :members:
   :show-inheritance:

Export
----------------------
.. autoclass:: redbrick.export.Export
   :members: export_tasks, search_tasks, get_task_events
   :show-inheritance:

Upload
----------------------
.. autoclass:: redbrick.upload.Upload
   :members: create_datapoints, delete_tasks, update_task_items
   :show-inheritance:

Labeling
----------------------
.. autoclass:: redbrick.labeling.Labeling
   :members: get_tasks, put_tasks, get_task_queue, assign_tasks, move_tasks_to_start
   :show-inheritance:
