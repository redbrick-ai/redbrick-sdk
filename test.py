import src as redbrick


api_key = "sHfLb_EMp14ByFTJj_ZjJBolzZgCKhZToPXWMbfVnyM"
url = "http://localhost:4000"
org_id = "fa670d97-0a74-4c35-aeea-bfb9b2c4d517"
project_id = "10dec73f-9f8b-4771-af21-f7e7a41b93df"
project = redbrick.get_project(api_key, url, org_id, project_id)

result = project.learning.get_learning_info()


print("RESULT", result)
