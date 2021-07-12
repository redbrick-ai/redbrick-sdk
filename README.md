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
"""redbrick quickstart."""
import redbrick

api_key = "<>"
url = "https://api.redbrickai.com"
org_id = "<>"
project_id = "<>"
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
failed_to_create = project.upload.create_datapoints(storage_id, datapoints)


# Datapoint object definition
{
    # REQUIRED: must be unique within a project
    "name": "my first upload",
    # List of urls or item paths, depending on your storage method
    "items": [
        "http://datasets.redbrickai.com/car-vids/car-1/frame20.png"
    ],
    # List of RedBrick Label objects
    "labels":  [<Label object>]

}


```

## Exporting data from your project

```python
import json

result = project.export.redbrick_format()

with open("export.json", "w+") as file_:
    json.dump(file_, result, indent=2)
```

### COCO Format

Coco format is supported for bounding box and polygon image projects. All other label types will be ignored.

To export into this format, use the following code snippet:

```python
coco_data = project.export.coco_format()

```

### Image masks

In order export into image masks for image segmentation projects, use the following:

```python
import os

project.export.png_masks(os.path("."))
```

This will produce a directory named "redbrick_masks" inside of the directory you specified.

## Active Learning

Each cycle of active learning involves three steps:

1. Data Export:

   - Get the unlabeled data, the labeled data, and the categories

2. Training, inference, and prioritization:

   - Using the labeled and unlabeled data, perform an algorithmic process to generate a score for each unlabeled datapoint float[0, 1].
   - Optionally generate labels to use as prelabels in the labeling process.

3. Upload results to RedBrick
   - Send the scores and optional labels to update your project

```python
# 1. Get data
data = project.learning.get_learning_info()
```

```
# 2. perform your processing
training(data["labeled"], data["taxonomy"])

results = inference_and_sort(data["unlabeled"], data["taxonomy"])
```

```
# 3. Update your project
project.learning.update_tasks(results)

```
