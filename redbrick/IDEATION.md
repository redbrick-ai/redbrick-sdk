Applications:

    - Export
        - Coco format
        - masks
    - Upload:
        - create datapoint
    - Labeling:
        - remote labeling

```python


import redbrick


project = redbrick.get_project(api_key, org_id, project_id)

project.learning.prepare()
project.learning.upload(tasks)

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

project.upload_images("./)


##########


project.export(
    download_data=False,
    separate_files=False,
    only_ground_truth=False,

)



learning = project.get_learning_stage("Active_Learning")

# check for job
#  get all the tasks
#        - training set (as coco format)
#        - unlabeled images



# gets the current cycle, either WAITING or QUEUED
# check the new points, if above client defined threshold, change state

# TODO: requires added logic to update status API, to manage state transition from WAITING TO QUEUED
# cycle = learning.get_cycle(force=False, minimum_of)

# cycle.prep_data("./training_data")

# # do training / inference

# cycle.upload_results(tasks=[
#     {"taskId": "asdasd","score": 0.5, "labels": [{"bbox2d": {}}]}
# ])


learning.get_data(file_path="", download_data=True, force=False, override_batch_size=100)

learning.upload_results(tasks)


# learning.annotations_file -> file path
# learning.images_folder
# learning.images_to_be_labeled -> dict/json object


<user_file_path>/project/stage_name/
    images/
        taskId.png
        taskId2.png
    all_images.json
        [{
            "name": "asdasd",
            "taskId": "asdasd",
            "filePath": "images/taskId.png"
        }]
    cycle_000001/
        annotations.json
        images_to_be_labeled.json

        classification_results.json
        detection_results.json
    cycle_000002/


project/stage_name/
    images/


```
