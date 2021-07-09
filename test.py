import redbrick
from uuid import uuid4

# from redbrick.converters iport coco


api_key = "l8LJvf6_yXZGUmU3ML6AOkO2Y7vABrSJrX7NQvN49U8"
url = "https://piljxrnf0h.execute-api.us-east-1.amazonaws.com/qa"
org_id = "9c7343fb-2fba-4d64-badc-8d573496403c"
project_id = "9c774b37-45f2-4845-bb3e-400ee446a297"
project = redbrick.get_project(api_key, url, org_id, project_id)


# create datapoints
# image_url = "http://datasets.redbrickai.com/car-vids/car-1/frame20.png"
# datapoints = [{"name": str(uuid4()), "items": [image_url]} for ii in range(500)]
# project.upload.create_datapoints("11111111-1111-1111-1111-111111111111", datapoints)


# label data
stage_name = "Label"

while True:
    tasks = project.labeling.get_tasks("Label", 50)
    tasks_labeled = [{"taskId": task["taskId"], "labels": []} for task in tasks]
    if tasks_labeled:
        project.labeling.put_tasks(stage_name, tasks_labeled)
