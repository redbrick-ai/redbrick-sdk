.. _sdk:

Python SDK
========================================
The SDK is best for writing Python scripts to interact with your RedBrick AI organization & projects. The SDK offers granular
functions for programmatically manipulating data, importing annotations, assigning tasks, and more.

RedBrick
----------------------
.. automodule:: redbrick
   :members: get_org, get_dataset, get_workspace, get_project, get_org_from_profile, get_dataset_from_profile, get_workspace_from_profile, get_project_from_profile, OrgMember, OrgInvite, ProjectMember, StorageProvider, StorageMethod, ImportTypes, TaskEventTypes, TaskFilters, TaskStates, Stage, LabelStage, ReviewStage, ModelStage
   :member-order: bysource

.. _org:

Organization
----------------------
.. autoclass:: redbrick.RBOrganization
   :members: name, org_id, create_dataset, create_workspace, create_project, create_project_advanced, get_dataset, get_project, workspaces_raw, projects_raw, projects, delete_dataset, archive_project, unarchive_project, delete_project, taxonomies, labeling_time, create_taxonomy, get_taxonomy, update_taxonomy, delete_taxonomy
   :show-inheritance:

Team
----------------------
.. autoclass:: redbrick.common.member.Team
   :members: get_member, list_members, disable_members, enable_members, list_invites, invite_user, revoke_invitation
   :show-inheritance:

Storage
----------------------
.. autoclass:: redbrick.common.storage.Storage
   :members: get_storage, list_storages, create_storage, update_storage, delete_storage, verify_storage
   :show-inheritance:

.. _dataset:

Dataset
----------------------
.. autoclass:: redbrick.RBDataset
   :members: dataset_name, org_id
   :show-inheritance:

DatasetUpload
----------------------
.. autoclass:: redbrick.common.upload.DatasetUpload
   :members: upload_files
   :show-inheritance:

DatasetExport
----------------------
.. autoclass:: redbrick.common.export.DatasetExport
   :members: get_data_store_series, export_to_files
   :show-inheritance:

.. _workspace:

Workspace
----------------------
.. autoclass:: redbrick.RBWorkspace
   :members: name, org_id, workspace_id, metadata_schema, classification_schema, cohorts, update_schema, update_cohorts, get_datapoints, create_datapoints, archive_datapoints, unarchive_datapoints, delete_datapoints, add_datapoints_to_cohort, add_datapoints_to_projects, remove_datapoints_from_cohort, update_datapoint_attributes, update_datapoints_metadata, import_from_dataset
   :show-inheritance:

.. _project:

Project
----------------------
.. autoclass:: redbrick.RBProject
   :members: name, org_id, project_id, url, taxonomy_name, taxonomy, workspace_id, label_storage, stages, set_label_storage, update_stage
   :show-inheritance:

Export
----------------------
.. autoclass:: redbrick.common.export.Export
   :members: export_tasks, list_tasks, get_task_events, get_active_time
   :show-inheritance:

Upload
----------------------
.. autoclass:: redbrick.common.upload.Upload
   :members: create_datapoints, delete_tasks, delete_tasks_by_name, update_task_items, import_tasks_from_workspace, update_tasks_priority, update_tasks_labels, send_tasks_to_stage, import_from_dataset, create_comment
   :show-inheritance:

Labeling
----------------------
.. autoclass:: redbrick.common.labeling.Labeling
   :members: put_tasks, assign_tasks, move_tasks_to_start
   :show-inheritance:

Settings
----------------------
.. autoclass:: redbrick.common.settings.Settings
   :members: label_validation, hanging_protocol, webhook, toggle_reference_standard_task, task_duplication
   :show-inheritance:

Workforce
----------------------
.. autoclass:: redbrick.common.member.Workforce
   :members: get_member, list_members, add_members, update_members, remove_members
   :show-inheritance:
