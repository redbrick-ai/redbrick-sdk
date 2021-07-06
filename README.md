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


# OR with labels
storage_id = "11111111-1111-1111-1111-111111111111"

datapoints = [
    {
        "name": "my first upload",
        "items": [
            "http://datasets.redbrickai.com/car-vids/car-1/frame20.png"
        ],
        "labels":  [<Label object>]

    }
]
failed_to_create = project.upload.create_datapoints(storage_id, datapoints)

```

## Exporting data from your project

```python
result = project.export.redbrick_format()

```

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
data = project.learning.get_learning_info()

training(data["labeled"], data["taxonomy"])

results = inference_and_sort(data["unlabeled"], data["taxonomy"])

project.learning.update_tasks(results)

```
