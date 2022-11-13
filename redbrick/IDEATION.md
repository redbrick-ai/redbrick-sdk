Applications:

    - Export
    - Upload:
        - create datapoint
    - Labeling:
        - remote labeling

```python


import redbrick


project = redbrick.get_project(api_key, org_id, project_id)

project.export(
    download_data=False,
    separate_files=False,
    only_ground_truth=False,
)

project.upload.create_datapoints()
# project.upload.upload_image()

project.labeling.get_tasks()
project.labeling.put_tasks()



# projects = client.get_projects()

# project = client.get_project(projects[0]["projectId"])

# project.get_stages()

# storage_methods = client.get_storage_methods()

project.create_datapoint(
    storage_methods[0]["storageId"],
    dpoint={"name": "dpoint name", "items": ["url.jpg"]}
)

project.upload_image("./my_img")

project.create_datapoints(
    storage_methods[0]["storageId"],
    dpoints=[{"name": "dpoint name", "items": []}...]
)

project.upload_images("./")


##########


project.export(
    download_data=False,
    separate_files=False,
    only_ground_truth=False,

)

```
