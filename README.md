# Introduction

This is an SDK to make integration with the RedBrick platform as easy as possible. This includes uploading and downloading data
as well as making your datasets easily available for training. Use this SDK to access your data and labels anywhere you run your code, whether that is on the cloud or locally with a Jupyter Notebook.

Please feel free to submit issues on github or at [support@redbrickai.com](mailto:support@redbrickai.com) if you run into any problems or have suggestions.

## Quickstart

After creating an account on [app.redbrickai.com](https://app.redbrick.com),

```bash
pip install --upgrade redbrick-sdk
```

You'll need to get your API key before you can utilize the SDK.

```python
"""redbrick-sdk quickstart, framework agnostic."""
import redbrick

api_key = "sHfLb_EMp14ByFTJj_ZjJBolzZgCKhZToPXWMbfVnyM"
url = "https://api.redbrickai.com"
org_id = "fa670d97-0a74-4c35-aeea-bfb9b2c4d517"
project_id = "10dec73f-9f8b-4771-af21-f7e7a41b93df"
project = redbrick.get_project(api_key, url, org_id, project_id)


```

## Importing data

There is a single way to import data into your project through the sdk. This is done using the create datapoint api.

An example using a "Public" storage method is given below

```python

# default public storage method
storage_id = "11111111-1111-1111-1111-111111111111"

datapoints = [
    {
        "name": "my first upload",
        "items": [
            "http://datasets.redbrickai.com/car-vids/car-1/frame20.png"
        ]
    }
]
project.upload.create_datapoints(storage_id, datapoints)

```
