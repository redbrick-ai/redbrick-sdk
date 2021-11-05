import redbrick
from redbrick.export import Export
import json
import matplotlib.pyplot as plt

api_key = "EGx3oXKIunzmxM7Tf12FweuKlfJY0ZDgZ-h2ilTNej4"
url = "https://api.redbrickai.com"
org_id = "3d0caac7-b1e9-483f-8676-c0aca73af232"
project_id = "d36ae4bd-c57f-41c6-ac3e-8116324b8091"

project = redbrick.get_project(api_key, url, org_id, project_id)
<<<<<<< HEAD
# project.upload.create_datapoints_from_masks("11111111-1111-1111-1111-111111111111", "redbrick/upload/mask_test")
=======
project.upload.create_datapoints_from_masks(
    "11111111-1111-1111-1111-111111111111", "test_mask"
)
>>>>>>> 5dd1ae654809b091a0fdaae46acae2457dc620c9

result = project.export.redbrick_format(
    True
)  # passing true will only export Completed tasks

# optional, save to file
import json
import os

path = os.path.join(os.path.curdir, "redbrick_export_segment.json")
with open(path, "w+") as file_:
    json.dump(result, file_)


# tasks = []
# with open("redbrick_export_segment.json", "r") as file:
#     tasks = json.load(file)

# tax = {
#     "name": "DEFAULT::Berkeley Deep Drive (BDD)",
#     "version": 1,
#     "categories": [
#         {
#             "name": "object",
#             "children": [
#                 {"name": "bus", "classId": 0, "children": []},
#                 {"name": "traffic light", "classId": 1, "children": []},
#                 {"name": "traffic sign", "classId": 2, "children": []},
#                 {"name": "person", "classId": 3, "children": []},
#                 {"name": "bike", "classId": 4, "children": []},
#                 {"name": "truck", "classId": 5, "children": []},
#                 {"name": "motor", "classId": 6, "children": []},
#                 {"name": "car", "classId": 7, "children": []},
#                 {"name": "train", "classId": 8, "children": []},
#                 {"name": "rider", "classId": 9, "children": []},
#             ],
#         }
#     ],
# }


# mask = project.export.convert_rbai_mask(tasks[0], tax)
# plt.imsave("mask.png", mask)


# fig, ax = plt.subplots()
# ax.imshow(mask)
# plt.show()
