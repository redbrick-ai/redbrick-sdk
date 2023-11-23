RedBrick AI SDK
========================================
The SDK is best for writing Python scripts to interact with your RedBrick AI organization & projects. The SDK offers granular
functions for programmatically manipulating data, importing annotations, assigning tasks, and more.

RedBrick
----------------------
.. automodule:: redbrick
   :members: get_org, get_workspace, get_project, StorageMethod, ImportTypes, TaskEventTypes, TaskFilters
   :show-inheritance:

Organization
----------------------
.. automodule:: redbrick.organization.RBOrganization
   :members: name, org_id, create_workspace, create_project, get_project, projects_raw, projects, labeling_time, create_taxonomy, get_taxonomy, update_taxonomy
   :show-inheritance:

Workspace
----------------------
.. automodule:: redbrick.workspace.RBWorkspace
   :members: name, org_id, workspace_id
   :show-inheritance:

Project
----------------------
.. autoclass:: redbrick.project.RBProject
   :members: name, org_id, project_id, url, taxonomy_name, workspace_id, label_storage, label_stages, review_stages, members, set_label_storage
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
