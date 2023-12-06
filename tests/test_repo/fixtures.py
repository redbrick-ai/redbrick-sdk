"""Fixtures for tests in `tests.test_repo.*`"""
import typing as t

# pylint: disable=line-too-long
# pylint: disable=pointless-string-statement
"""
MOCK API RESPONSES for tests

Unless explicitly stated, the following args are sent with concerned call

    stage_name = "Review_1"
    task_id = "6a12cb11-ce37-43a1-b8b6-20b1317afffd"
    dp_id = "3037045c-ca3c-4bb4-8b87-8ea2d45c6b34"
    storage_id = "11111111-1111-1111-1111-111111111111"

"""
datapoints_in_project_resp = {"tasksPaged": {"count": 7}}


def get_datapoint_latest_resp(task_id):  # noqa: D103
    """Mock response for `ExportRepo.get_datapoint_latest`"""
    resp = {
        "task": {
            "currentStageName": "Label",
            "currentStageSubTask": {
                "assignedTo": {
                    "email": "mock@email.com",
                    "userId": "1c643889-5a8b-4b20-8e48-14e9cbd5eeb7",
                },
                "consensusInfo": [
                    {
                        "scores": [],
                        "taskData": {
                            "createdAt": "2023-10-20T14:31:38.610700+00:00",
                            "createdByEmail": "mock@email.com",
                            "labelsData": "[]",
                            "labelsMap": None,
                            "labelsStorage": {
                                "storageId": "22222222-2222-2222-2222-222222222222"
                            },
                        },
                        "user": {
                            "email": "",
                            "userId": "API:08f698f7-4cf3-4299-bb83-52a3fe9c7517",
                        },
                    }
                ],
                "overallConsensusScore": None,
                "state": "ASSIGNED",
                "subTasks": [],
                "taskData": {
                    "createdAt": "2023-10-20T14:31:38.610700+00:00",
                    "createdByEmail": "mock@email.com",
                    "labelsData": "[]",
                    "labelsMap": None,
                    "labelsStorage": {
                        "storageId": "22222222-2222-2222-2222-222222222222"
                    },
                },
            },
            "dpId": "b76d5137-3cb2-4496-91e3-bc1defaab99d",
            "latestTaskData": {
                "createdAt": "2023-10-20T14:31:38.610700+00:00",
                "createdByEmail": "mock@email.com",
                "dataPoint": {
                    "createdAt": "2023-10-20T14:31:38.610645+00:00",
                    "createdByEntity": {
                        "email": "mock@email.com",
                        "userId": "1c643889-5a8b-4b20-8e48-14e9cbd5eeb7",
                    },
                    "items": [
                        "https://mock.com/some_randon_image/BraTS2021_00003/BraTS2021_00003_t2.nii.gz",
                        "https://mock.com/some_randon_image/BraTS2021_00003/BraTS2021_00003_t1ce.nii.gz",
                        "https://mock.com/some_randon_image/BraTS2021_00003/BraTS2021_00003_t1.nii.gz",
                        "https://mock.com/some_randon_image/BraTS2021_00003/BraTS2021_00003_flair.nii.gz",
                    ],
                    "metaData": None,
                    "name": "BraTS2021_00003",
                    "seriesInfo": [
                        {
                            "dataType": "nifti",
                            "itemsIndices": [0],
                            "metaData": None,
                            "name": None,
                        },
                        {
                            "dataType": "nifti",
                            "itemsIndices": [1],
                            "metaData": None,
                            "name": None,
                        },
                        {
                            "dataType": "nifti",
                            "itemsIndices": [2],
                            "metaData": None,
                            "name": None,
                        },
                        {
                            "dataType": "nifti",
                            "itemsIndices": [3],
                            "metaData": None,
                            "name": None,
                        },
                    ],
                    "storageMethod": {
                        "storageId": "11111111-1111-1111-1111-111111111111"
                    },
                },
                "labelsData": "[]",
                "labelsMap": None,
                "labelsStorage": {"storageId": "22222222-2222-2222-2222-222222222222"},
            },
            "priority": None,
            "taskId": task_id,
        }
    }
    return resp


get_datapoints_latest_resp: t.Dict[str, t.Any] = {
    "tasksPaged": {
        "cacheTime": None,
        "cursor": None,
        "entries": [
            {
                "taskId": "682c8185-1e9d-4c49-b98d-869971c9304a",
                "dpId": "add792f9-8965-4ee6-b09d-c5bd34cb01bf",
                "currentStageName": "Label",
                "priority": None,
                "currentStageSubTask": {
                    "state": "ASSIGNED",
                    "assignedTo": {
                        "userId": "1c643889-5a8b-4b20-8e48-14e9cbd5eeb7",
                        "email": "mock@email.com",
                    },
                    "taskData": {
                        "createdAt": "2023-10-20T14:31:38.610835+00:00",
                        "createdByEmail": "mock@email.com",
                        "labelsData": "[]",
                        "labelsStorage": {
                            "storageId": "22222222-2222-2222-2222-222222222222"
                        },
                        "labelsMap": None,
                    },
                    "subTasks": [],
                    "overallConsensusScore": None,
                    "consensusInfo": [
                        {
                            "user": {
                                "userId": "API:08f698f7-4cf3-4299-bb83-52a3fe9c7517",
                                "email": "",
                            },
                            "taskData": {
                                "createdAt": "2023-10-20T14:31:38.610835+00:00",
                                "createdByEmail": "mock@email.com",
                                "labelsData": "[]",
                                "labelsStorage": {
                                    "storageId": "22222222-2222-2222-2222-222222222222"
                                },
                                "labelsMap": None,
                            },
                            "scores": [],
                        }
                    ],
                },
                "latestTaskData": {
                    "dataPoint": {
                        "name": "BraTS2021_00009",
                        "items": [
                            "https://mock.com/some_randon_image/BraTS2021_00009/BraTS2021_00009_t2.nii.gz",
                            "https://mock.com/some_randon_image/BraTS2021_00009/BraTS2021_00009_t1ce.nii.gz",
                            "https://mock.com/some_randon_image/BraTS2021_00009/BraTS2021_00009_flair.nii.gz",
                            "https://mock.com/some_randon_image/BraTS2021_00009/BraTS2021_00009_t1.nii.gz",
                        ],
                        "createdAt": "2023-10-20T14:31:38.610819+00:00",
                        "createdByEntity": {
                            "userId": "1c643889-5a8b-4b20-8e48-14e9cbd5eeb7",
                            "email": "mock@email.com",
                        },
                        "metaData": None,
                        "seriesInfo": None,
                        "storageMethod": {
                            "storageId": "11111111-1111-1111-1111-111111111111"
                        },
                    },
                    "createdAt": "2023-10-20T14:31:38.610835+00:00",
                    "createdByEmail": "mock@email.com",
                    "labelsData": "[]",
                    "labelsStorage": {
                        "storageId": "22222222-2222-2222-2222-222222222222"
                    },
                    "labelsMap": None,
                },
            },
            {
                "taskId": "af454bb5-9fc8-4b22-a2b9-033d49e28539",
                "dpId": "b76d5137-3cb2-4496-91e3-bc1defaab99d",
                "currentStageName": "Label",
                "priority": None,
                "currentStageSubTask": {
                    "state": "ASSIGNED",
                    "assignedTo": {
                        "userId": "1c643889-5a8b-4b20-8e48-14e9cbd5eeb7",
                        "email": "mock@email.com",
                    },
                    "taskData": {
                        "createdAt": "2023-10-20T14:31:38.610700+00:00",
                        "createdByEmail": "mock@email.com",
                        "labelsData": "[]",
                        "labelsStorage": {
                            "storageId": "22222222-2222-2222-2222-222222222222"
                        },
                        "labelsMap": None,
                    },
                    "subTasks": [],
                    "overallConsensusScore": None,
                    "consensusInfo": [
                        {
                            "user": {
                                "userId": "API:08f698f7-4cf3-4299-bb83-52a3fe9c7517",
                                "email": "",
                            },
                            "taskData": {
                                "createdAt": "2023-10-20T14:31:38.610700+00:00",
                                "createdByEmail": "mock@email.com",
                                "labelsData": "[]",
                                "labelsStorage": {
                                    "storageId": "22222222-2222-2222-2222-222222222222"
                                },
                                "labelsMap": None,
                            },
                            "scores": [],
                        }
                    ],
                },
                "latestTaskData": {
                    "dataPoint": {
                        "name": "BraTS2021_00003",
                        "items": [
                            "https://mock.com/some_randon_image/BraTS2021_00003/BraTS2021_00003_t2.nii.gz",
                            "https://mock.com/some_randon_image/BraTS2021_00003/BraTS2021_00003_t1ce.nii.gz",
                            "https://mock.com/some_randon_image/BraTS2021_00003/BraTS2021_00003_t1.nii.gz",
                            "https://mock.com/some_randon_image/BraTS2021_00003/BraTS2021_00003_flair.nii.gz",
                        ],
                        "createdAt": "2023-10-20T14:31:38.610645+00:00",
                        "createdByEntity": {
                            "userId": "1c643889-5a8b-4b20-8e48-14e9cbd5eeb7",
                            "email": "mock@email.com",
                        },
                        "metaData": None,
                        "seriesInfo": [
                            {
                                "name": None,
                                "itemsIndices": [0],
                                "dataType": "nifti",
                                "metaData": None,
                            },
                            {
                                "name": None,
                                "itemsIndices": [1],
                                "dataType": "nifti",
                                "metaData": None,
                            },
                            {
                                "name": None,
                                "itemsIndices": [2],
                                "dataType": "nifti",
                                "metaData": None,
                            },
                            {
                                "name": None,
                                "itemsIndices": [3],
                                "dataType": "nifti",
                                "metaData": None,
                            },
                        ],
                        "storageMethod": {
                            "storageId": "11111111-1111-1111-1111-111111111111"
                        },
                    },
                    "createdAt": "2023-10-20T14:31:38.610700+00:00",
                    "createdByEmail": "mock@email.com",
                    "labelsData": "[]",
                    "labelsStorage": {
                        "storageId": "22222222-2222-2222-2222-222222222222"
                    },
                    "labelsMap": None,
                },
            },
            {
                "taskId": "6a12cb11-ce37-43a1-b8b6-20b1317afffd",
                "dpId": "3037045c-ca3c-4bb4-8b87-8ea2d45c6b34",
                "currentStageName": "Review_1",
                "priority": None,
                "currentStageSubTask": {
                    "state": "UNASSIGNED",
                    "assignedTo": None,
                    "taskData": {
                        "createdAt": "2023-10-20T14:33:27.664115+00:00",
                        "createdByEmail": "mock@email.com",
                        "labelsData": '[{"category":"liver","attributes":[],"classid":0,"labelid":"7f138361-dad9-4a90-853a-cf030a605221","bbox2d":null,"point":null,"polyline":null,"polygon":null,"pixel":null,"ellipse":null,"dicom":{"instanceid":1,"groupids":null},"point3d":null,"bbox3d":null,"length3d":null,"angle3d":null,"volumeindex":0,"frameclassify":null,"taskclassify":null,"tasklevelclassify":null,"multiclassify":null,"frameindex":null,"trackid":null,"keyframe":null,"end":null,"dummy":null,"confidence":null,"ocrvalue":null,"studyclassify":null,"seriesclassify":null,"instanceclassify":null,"stats":null},{"category":"lung","attributes":[],"classid":1,"labelid":"302a87fc-eabd-402e-a95e-9c32529d2901","bbox2d":null,"point":null,"polyline":null,"polygon":null,"pixel":null,"ellipse":null,"dicom":{"instanceid":1,"groupids":null},"point3d":null,"bbox3d":null,"length3d":null,"angle3d":null,"volumeindex":3,"frameclassify":null,"taskclassify":null,"tasklevelclassify":null,"multiclassify":null,"frameindex":null,"trackid":null,"keyframe":null,"end":null,"dummy":null,"confidence":null,"ocrvalue":null,"studyclassify":null,"seriesclassify":null,"instanceclassify":null,"stats":null},{"category":null,"attributes":[],"classid":null,"labelid":"d775111e-7a47-445e-9f46-dd84cd64b8ba","bbox2d":null,"point":null,"polyline":null,"polygon":null,"pixel":null,"ellipse":null,"dicom":null,"point3d":null,"bbox3d":null,"length3d":null,"angle3d":null,"volumeindex":null,"frameclassify":null,"taskclassify":null,"tasklevelclassify":null,"multiclassify":null,"frameindex":null,"trackid":null,"keyframe":null,"end":null,"dummy":null,"confidence":null,"ocrvalue":null,"studyclassify":true,"seriesclassify":null,"instanceclassify":null,"stats":null}]',  # noqa: E501
                        "labelsStorage": {
                            "storageId": "22222222-2222-2222-2222-222222222222"
                        },
                        "labelsMap": [
                            {
                                "imageIndex": 0,
                                "labelName": "c78d312f-5b41-4b66-9c06-44c375abe057/75a0af6f-4f48-46dd-a4d2-1b43ea238559/labels/6a12cb11-ce37-43a1-b8b6-20b1317afffd/nifti/80feaafb-2456-48fb-833f-2012138a63e7",  # noqa: E501
                            },
                            {
                                "imageIndex": 3,
                                "labelName": "c78d312f-5b41-4b66-9c06-44c375abe057/75a0af6f-4f48-46dd-a4d2-1b43ea238559/labels/6a12cb11-ce37-43a1-b8b6-20b1317afffd/nifti/73d5388a-d742-43c9-950e-29fc116527e7",  # noqa: E501
                            },
                        ],
                    },
                    "subTasks": [],
                    "overallConsensusScore": None,
                    "consensusInfo": [
                        {
                            "user": {
                                "userId": "API:08f698f7-4cf3-4299-bb83-52a3fe9c7517",
                                "email": "",
                            },
                            "taskData": {
                                "createdAt": "2023-10-20T14:33:27.664115+00:00",
                                "createdByEmail": "mock@email.com",
                                "labelsData": '[{"category":"liver","attributes":[],"classid":0,"labelid":"7f138361-dad9-4a90-853a-cf030a605221","bbox2d":null,"point":null,"polyline":null,"polygon":null,"pixel":null,"ellipse":null,"dicom":{"instanceid":1,"groupids":null},"point3d":null,"bbox3d":null,"length3d":null,"angle3d":null,"volumeindex":0,"frameclassify":null,"taskclassify":null,"tasklevelclassify":null,"multiclassify":null,"frameindex":null,"trackid":null,"keyframe":null,"end":null,"dummy":null,"confidence":null,"ocrvalue":null,"studyclassify":null,"seriesclassify":null,"instanceclassify":null,"stats":null},{"category":"lung","attributes":[],"classid":1,"labelid":"302a87fc-eabd-402e-a95e-9c32529d2901","bbox2d":null,"point":null,"polyline":null,"polygon":null,"pixel":null,"ellipse":null,"dicom":{"instanceid":1,"groupids":null},"point3d":null,"bbox3d":null,"length3d":null,"angle3d":null,"volumeindex":3,"frameclassify":null,"taskclassify":null,"tasklevelclassify":null,"multiclassify":null,"frameindex":null,"trackid":null,"keyframe":null,"end":null,"dummy":null,"confidence":null,"ocrvalue":null,"studyclassify":null,"seriesclassify":null,"instanceclassify":null,"stats":null},{"category":null,"attributes":[],"classid":null,"labelid":"d775111e-7a47-445e-9f46-dd84cd64b8ba","bbox2d":null,"point":null,"polyline":null,"polygon":null,"pixel":null,"ellipse":null,"dicom":null,"point3d":null,"bbox3d":null,"length3d":null,"angle3d":null,"volumeindex":null,"frameclassify":null,"taskclassify":null,"tasklevelclassify":null,"multiclassify":null,"frameindex":null,"trackid":null,"keyframe":null,"end":null,"dummy":null,"confidence":null,"ocrvalue":null,"studyclassify":true,"seriesclassify":null,"instanceclassify":null,"stats":null}]',  # noqa: E501
                                "labelsStorage": {
                                    "storageId": "22222222-2222-2222-2222-222222222222"
                                },
                                "labelsMap": [
                                    {
                                        "imageIndex": 0,
                                        "labelName": "c78d312f-5b41-4b66-9c06-44c375abe057/75a0af6f-4f48-46dd-a4d2-1b43ea238559/labels/6a12cb11-ce37-43a1-b8b6-20b1317afffd/nifti/80feaafb-2456-48fb-833f-2012138a63e7",  # noqa: E501
                                    },
                                    {
                                        "imageIndex": 3,
                                        "labelName": "c78d312f-5b41-4b66-9c06-44c375abe057/75a0af6f-4f48-46dd-a4d2-1b43ea238559/labels/6a12cb11-ce37-43a1-b8b6-20b1317afffd/nifti/73d5388a-d742-43c9-950e-29fc116527e7",  # noqa: E501
                                    },
                                ],
                            },
                            "scores": [],
                        }
                    ],
                },
                "latestTaskData": {
                    "dataPoint": {
                        "name": "BraTS2021_00006",
                        "items": [
                            "https://mock.com/some_randon_image/BraTS2021_00006/BraTS2021_00006_t1.nii.gz",
                            "https://mock.com/some_randon_image/BraTS2021_00006/BraTS2021_00006_flair.nii.gz",
                            "https://mock.com/some_randon_image/BraTS2021_00006/BraTS2021_00006_t1ce.nii.gz",
                            "https://mock.com/some_randon_image/BraTS2021_00006/BraTS2021_00006_t2.nii.gz",
                        ],
                        "createdAt": "2023-10-20T14:31:38.610885+00:00",
                        "createdByEntity": {
                            "userId": "1c643889-5a8b-4b20-8e48-14e9cbd5eeb7",
                            "email": "mock@email.com",
                        },
                        "metaData": None,
                        "seriesInfo": [
                            {
                                "name": None,
                                "itemsIndices": [0],
                                "dataType": "nifti",
                                "metaData": None,
                            },
                            {
                                "name": None,
                                "itemsIndices": [1],
                                "dataType": "nifti",
                                "metaData": None,
                            },
                            {
                                "name": None,
                                "itemsIndices": [2],
                                "dataType": "nifti",
                                "metaData": None,
                            },
                            {
                                "name": None,
                                "itemsIndices": [3],
                                "dataType": "nifti",
                                "metaData": None,
                            },
                        ],
                        "storageMethod": {
                            "storageId": "11111111-1111-1111-1111-111111111111"
                        },
                    },
                    "createdAt": "2023-10-20T14:33:27.664115+00:00",
                    "createdByEmail": "mock@email.com",
                    "labelsData": '[{"category":"liver","attributes":[],"classid":0,"labelid":"7f138361-dad9-4a90-853a-cf030a605221","bbox2d":null,"point":null,"polyline":null,"polygon":null,"pixel":null,"ellipse":null,"dicom":{"instanceid":1,"groupids":null},"point3d":null,"bbox3d":null,"length3d":null,"angle3d":null,"volumeindex":0,"frameclassify":null,"taskclassify":null,"tasklevelclassify":null,"multiclassify":null,"frameindex":null,"trackid":null,"keyframe":null,"end":null,"dummy":null,"confidence":null,"ocrvalue":null,"studyclassify":null,"seriesclassify":null,"instanceclassify":null,"stats":null},{"category":"lung","attributes":[],"classid":1,"labelid":"302a87fc-eabd-402e-a95e-9c32529d2901","bbox2d":null,"point":null,"polyline":null,"polygon":null,"pixel":null,"ellipse":null,"dicom":{"instanceid":1,"groupids":null},"point3d":null,"bbox3d":null,"length3d":null,"angle3d":null,"volumeindex":3,"frameclassify":null,"taskclassify":null,"tasklevelclassify":null,"multiclassify":null,"frameindex":null,"trackid":null,"keyframe":null,"end":null,"dummy":null,"confidence":null,"ocrvalue":null,"studyclassify":null,"seriesclassify":null,"instanceclassify":null,"stats":null},{"category":null,"attributes":[],"classid":null,"labelid":"d775111e-7a47-445e-9f46-dd84cd64b8ba","bbox2d":null,"point":null,"polyline":null,"polygon":null,"pixel":null,"ellipse":null,"dicom":null,"point3d":null,"bbox3d":null,"length3d":null,"angle3d":null,"volumeindex":null,"frameclassify":null,"taskclassify":null,"tasklevelclassify":null,"multiclassify":null,"frameindex":null,"trackid":null,"keyframe":null,"end":null,"dummy":null,"confidence":null,"ocrvalue":null,"studyclassify":true,"seriesclassify":null,"instanceclassify":null,"stats":null}]',  # noqa: E501
                    "labelsStorage": {
                        "storageId": "22222222-2222-2222-2222-222222222222"
                    },
                    "labelsMap": [
                        {
                            "imageIndex": 0,
                            "labelName": "c78d312f-5b41-4b66-9c06-44c375abe057/75a0af6f-4f48-46dd-a4d2-1b43ea238559/labels/6a12cb11-ce37-43a1-b8b6-20b1317afffd/nifti/80feaafb-2456-48fb-833f-2012138a63e7",  # noqa: E501
                        },
                        {
                            "imageIndex": 3,
                            "labelName": "c78d312f-5b41-4b66-9c06-44c375abe057/75a0af6f-4f48-46dd-a4d2-1b43ea238559/labels/6a12cb11-ce37-43a1-b8b6-20b1317afffd/nifti/73d5388a-d742-43c9-950e-29fc116527e7",  # noqa: E501
                        },
                    ],
                },
            },
            {
                "taskId": "2067f35a-90e6-4243-965d-8d64868021bd",
                "dpId": "9b97c9c1-eebb-4e5f-b969-1da2bdb18d49",
                "currentStageName": "END",
                "priority": None,
                "currentStageSubTask": None,
                "latestTaskData": {
                    "dataPoint": {
                        "name": "BraTS2021_00005",
                        "items": [
                            "https://mock.com/some_randon_image/BraTS2021_00005/BraTS2021_00005_t1ce.nii.gz",
                            "https://mock.com/some_randon_image/BraTS2021_00005/BraTS2021_00005_t2.nii.gz",
                            "https://mock.com/some_randon_image/BraTS2021_00005/BraTS2021_00005_flair.nii.gz",
                            "https://mock.com/some_randon_image/BraTS2021_00005/BraTS2021_00005_t1.nii.gz",
                        ],
                        "createdAt": "2023-10-20T14:31:38.610727+00:00",
                        "createdByEntity": {
                            "userId": "1c643889-5a8b-4b20-8e48-14e9cbd5eeb7",
                            "email": "mock@email.com",
                        },
                        "metaData": None,
                        "seriesInfo": [
                            {
                                "name": None,
                                "itemsIndices": [0],
                                "dataType": "nifti",
                                "metaData": None,
                            },
                            {
                                "name": None,
                                "itemsIndices": [1],
                                "dataType": "nifti",
                                "metaData": None,
                            },
                            {
                                "name": None,
                                "itemsIndices": [2],
                                "dataType": "nifti",
                                "metaData": None,
                            },
                            {
                                "name": None,
                                "itemsIndices": [3],
                                "dataType": "nifti",
                                "metaData": None,
                            },
                        ],
                        "storageMethod": {
                            "storageId": "11111111-1111-1111-1111-111111111111"
                        },
                    },
                    "createdAt": "2023-10-20T14:32:32.204050+00:00",
                    "createdByEmail": "mock@email.com",
                    "labelsData": '[{"category":"liver","attributes":[],"classid":0,"labelid":"5542d87c-c0d2-49ca-a7d8-c04f825c7a32","bbox2d":null,"point":null,"polyline":null,"polygon":null,"pixel":null,"ellipse":null,"dicom":{"instanceid":1,"groupids":null},"point3d":null,"bbox3d":null,"length3d":null,"angle3d":null,"volumeindex":0,"frameclassify":null,"taskclassify":null,"tasklevelclassify":null,"multiclassify":null,"frameindex":null,"trackid":null,"keyframe":null,"end":null,"dummy":null,"confidence":null,"ocrvalue":null,"studyclassify":null,"seriesclassify":null,"instanceclassify":null,"stats":null},{"category":"lung","attributes":[],"classid":1,"labelid":"89f52268-c5fb-40a3-ad88-0a3720854028","bbox2d":null,"point":null,"polyline":null,"polygon":null,"pixel":null,"ellipse":null,"dicom":{"instanceid":1,"groupids":null},"point3d":null,"bbox3d":null,"length3d":null,"angle3d":null,"volumeindex":1,"frameclassify":null,"taskclassify":null,"tasklevelclassify":null,"multiclassify":null,"frameindex":null,"trackid":null,"keyframe":null,"end":null,"dummy":null,"confidence":null,"ocrvalue":null,"studyclassify":null,"seriesclassify":null,"instanceclassify":null,"stats":null},{"category":"kidney","attributes":[],"classid":2,"labelid":"ebaf2efc-3460-4115-b0a2-b4b5c237e19f","bbox2d":null,"point":null,"polyline":null,"polygon":null,"pixel":null,"ellipse":null,"dicom":{"instanceid":1,"groupids":null},"point3d":null,"bbox3d":null,"length3d":null,"angle3d":null,"volumeindex":2,"frameclassify":null,"taskclassify":null,"tasklevelclassify":null,"multiclassify":null,"frameindex":null,"trackid":null,"keyframe":null,"end":null,"dummy":null,"confidence":null,"ocrvalue":null,"studyclassify":null,"seriesclassify":null,"instanceclassify":null,"stats":null},{"category":null,"attributes":[],"classid":null,"labelid":"22d4cfc6-fe75-482c-8448-c377163bd66d","bbox2d":null,"point":null,"polyline":null,"polygon":null,"pixel":null,"ellipse":null,"dicom":null,"point3d":null,"bbox3d":null,"length3d":null,"angle3d":null,"volumeindex":null,"frameclassify":null,"taskclassify":null,"tasklevelclassify":null,"multiclassify":null,"frameindex":null,"trackid":null,"keyframe":null,"end":null,"dummy":null,"confidence":null,"ocrvalue":null,"studyclassify":true,"seriesclassify":null,"instanceclassify":null,"stats":null}]',  # noqa: E501
                    "labelsStorage": {
                        "storageId": "22222222-2222-2222-2222-222222222222"
                    },
                    "labelsMap": [
                        {
                            "imageIndex": 0,
                            "labelName": "c78d312f-5b41-4b66-9c06-44c375abe057/75a0af6f-4f48-46dd-a4d2-1b43ea238559/labels/2067f35a-90e6-4243-965d-8d64868021bd/nifti/b59f0317-47d3-43bc-bdd2-a2eb965c6a9c",  # noqa: E501
                        },
                        {
                            "imageIndex": 1,
                            "labelName": "c78d312f-5b41-4b66-9c06-44c375abe057/75a0af6f-4f48-46dd-a4d2-1b43ea238559/labels/2067f35a-90e6-4243-965d-8d64868021bd/nifti/671ca60f-179e-42c9-9dca-9d3fdfc13ec7",  # noqa: E501
                        },
                        {
                            "imageIndex": 2,
                            "labelName": "c78d312f-5b41-4b66-9c06-44c375abe057/75a0af6f-4f48-46dd-a4d2-1b43ea238559/labels/2067f35a-90e6-4243-965d-8d64868021bd/nifti/d4cdaa0b-faa9-4665-adf0-88c77785ba1b",  # noqa: E501
                        },
                    ],
                },
            },
        ],
    },
}


def task_search_resp(mock_stage_name):  # noqa: D103
    """Mock response for `ExportRepo.task_search`"""
    resp = {
        "genericTasks": {
            "entries": [
                {
                    "taskId": "6a12cb11-ce37-43a1-b8b6-20b1317afffd",
                    "currentStageName": mock_stage_name,
                    "createdAt": "2023-10-20T14:31:39.393522+00:00",
                    "updatedAt": "2023-10-20T14:33:28.427885+00:00",
                    "priority": None,
                    "datapoint": {
                        "name": "BraTS2021_00006",
                        "createdAt": "2023-10-20T14:31:38.610885+00:00",
                        "createdByEntity": {
                            "userId": "1c643889-5a8b-4b20-8e48-14e9cbd5eeb7",
                            "email": "mock@email.com",
                        },
                        "metaData": None,
                        "seriesInfo": [
                            {
                                "name": None,
                                "itemsIndices": [0],
                                "dataType": "nifti",
                                "metaData": None,
                            },
                            {
                                "name": None,
                                "itemsIndices": [1],
                                "dataType": "nifti",
                                "metaData": None,
                            },
                            {
                                "name": None,
                                "itemsIndices": [2],
                                "dataType": "nifti",
                                "metaData": None,
                            },
                            {
                                "name": None,
                                "itemsIndices": [3],
                                "dataType": "nifti",
                                "metaData": None,
                            },
                        ],
                        "storageMethod": {
                            "storageId": "11111111-1111-1111-1111-111111111111"
                        },
                    },
                    "currentStageSubTask": {
                        "state": "UNASSIGNED",
                        "assignedTo": None,
                        "assignedAt": None,
                        "completedAt": None,
                        "completionTimeMs": None,
                        "progressSavedAt": None,
                        "subTasks": [],
                    },
                }
            ],
            "cursor": None,
        }
    }
    return resp


def presign_items_resp(items: t.Optional[t.List[str]] = None):
    """Mock response for `ExportRepo.presign_items`"""
    items = items or ["mock_item"]
    return {"presignItems": items}


task_events_resp = {
    "tasksPaged": {
        "entries": [
            {
                "taskId": "6a12cb11-ce37-43a1-b8b6-20b1317afffd",
                "currentStageName": "Review_1",
                "datapoint": {"name": "BraTS2021_00006"},
                "genericEvents": [
                    {
                        "__typename": "TaskEvent",
                        "eventId": "7c986854-b360-4544-a2c6-71723044c6c4",
                        "createdAt": "2023-10-20T14:31:39.422420+00:00",
                        "inputEvent": None,
                        "outputEvent": None,
                        "createEvent": {
                            "currentStageName": "Input",
                            "isGroundTruth": False,
                        },
                        "taskData": {
                            "stageName": "Input",
                            "createdBy": "1c643889-5a8b-4b20-8e48-14e9cbd5eeb7",
                        },
                    },
                    {
                        "__typename": "TaskEvent",
                        "eventId": "38dae1f7-dc36-4ff5-b8ae-d4eecc11a230",
                        "createdAt": "2023-10-20T14:31:39.700197+00:00",
                        "inputEvent": {
                            "currentStageName": "Label",
                            "overallConsensusScore": None,
                        },
                        "outputEvent": None,
                        "createEvent": None,
                        "taskData": {
                            "stageName": "Label",
                            "createdBy": "1c643889-5a8b-4b20-8e48-14e9cbd5eeb7",
                        },
                    },
                    {
                        "__typename": "TaskStateChanges",
                        "stageNameAfter": "Label",
                        "assignedAtAfter": "2023-10-20T14:31:54.065251+00:00",
                        "createdAt": "2023-10-20T14:31:54.133802+00:00",
                        "statusBefore": "UNASSIGNED",
                        "statusAfter": "ASSIGNED",
                        "assignedToBefore": None,
                        "assignedToAfter": "1c643889-5a8b-4b20-8e48-14e9cbd5eeb7",
                        "consensusAssigneesBefore": [],
                        "consensusAssigneesAfter": [],
                        "consensusStatusesBefore": [],
                        "consensusStatusesAfter": [],
                    },
                    {
                        "__typename": "TaskStateChanges",
                        "stageNameAfter": "Label",
                        "assignedAtAfter": "2023-10-20T14:31:54.065251+00:00",
                        "createdAt": "2023-10-20T14:33:27.906925+00:00",
                        "statusBefore": "ASSIGNED",
                        "statusAfter": "COMPLETED",
                        "assignedToBefore": "1c643889-5a8b-4b20-8e48-14e9cbd5eeb7",
                        "assignedToAfter": "1c643889-5a8b-4b20-8e48-14e9cbd5eeb7",
                        "consensusAssigneesBefore": [],
                        "consensusAssigneesAfter": [],
                        "consensusStatusesBefore": [],
                        "consensusStatusesAfter": [],
                    },
                    {
                        "__typename": "TaskEvent",
                        "eventId": "35bc57ee-44c8-476f-82db-eec3968a99df",
                        "createdAt": "2023-10-20T14:33:27.971766+00:00",
                        "inputEvent": None,
                        "outputEvent": {
                            "currentStageName": "Label",
                            "outputBool": None,
                        },
                        "createEvent": None,
                        "taskData": {
                            "stageName": "Label",
                            "createdBy": "1c643889-5a8b-4b20-8e48-14e9cbd5eeb7",
                        },
                    },
                    {
                        "__typename": "TaskEvent",
                        "eventId": "1b567611-8a1d-4d7b-9ef0-72b80e30ec36",
                        "createdAt": "2023-10-20T14:33:28.409084+00:00",
                        "inputEvent": {
                            "currentStageName": "Review_1",
                            "overallConsensusScore": None,
                        },
                        "outputEvent": None,
                        "createEvent": None,
                        "taskData": {
                            "stageName": "Review_1",
                            "createdBy": "1c643889-5a8b-4b20-8e48-14e9cbd5eeb7",
                        },
                    },
                ],
            },
            {
                "taskId": "2067f35a-90e6-4243-965d-8d64868021bd",
                "currentStageName": "END",
                "datapoint": {"name": "BraTS2021_00005"},
                "genericEvents": [
                    {
                        "__typename": "TaskEvent",
                        "eventId": "eeebc742-4a3b-4960-9cc2-4f2a5d644a2e",
                        "createdAt": "2023-10-20T14:31:44.252197+00:00",
                        "inputEvent": None,
                        "outputEvent": None,
                        "createEvent": {
                            "currentStageName": "Input",
                            "isGroundTruth": False,
                        },
                        "taskData": {
                            "stageName": "Input",
                            "createdBy": "1c643889-5a8b-4b20-8e48-14e9cbd5eeb7",
                        },
                    },
                    {
                        "__typename": "TaskEvent",
                        "eventId": "2ba390fa-6d4c-4497-8e2e-c62a94ec3666",
                        "createdAt": "2023-10-20T14:31:44.656307+00:00",
                        "inputEvent": {
                            "currentStageName": "Label",
                            "overallConsensusScore": None,
                        },
                        "outputEvent": None,
                        "createEvent": None,
                        "taskData": {
                            "stageName": "Label",
                            "createdBy": "1c643889-5a8b-4b20-8e48-14e9cbd5eeb7",
                        },
                    },
                    {
                        "__typename": "TaskStateChanges",
                        "stageNameAfter": "Label",
                        "assignedAtAfter": "2023-10-20T14:31:49.541032+00:00",
                        "createdAt": "2023-10-20T14:31:49.584739+00:00",
                        "statusBefore": "UNASSIGNED",
                        "statusAfter": "ASSIGNED",
                        "assignedToBefore": None,
                        "assignedToAfter": "1c643889-5a8b-4b20-8e48-14e9cbd5eeb7",
                        "consensusAssigneesBefore": [],
                        "consensusAssigneesAfter": [],
                        "consensusStatusesBefore": [],
                        "consensusStatusesAfter": [],
                    },
                    {
                        "__typename": "TaskStateChanges",
                        "stageNameAfter": "Label",
                        "assignedAtAfter": "2023-10-20T14:31:49.541032+00:00",
                        "createdAt": "2023-10-20T14:32:32.487699+00:00",
                        "statusBefore": "ASSIGNED",
                        "statusAfter": "COMPLETED",
                        "assignedToBefore": "1c643889-5a8b-4b20-8e48-14e9cbd5eeb7",
                        "assignedToAfter": "1c643889-5a8b-4b20-8e48-14e9cbd5eeb7",
                        "consensusAssigneesBefore": [],
                        "consensusAssigneesAfter": [],
                        "consensusStatusesBefore": [],
                        "consensusStatusesAfter": [],
                    },
                    {
                        "__typename": "TaskEvent",
                        "eventId": "c8d5ef0b-58a9-4b92-8074-5e9ca985e867",
                        "createdAt": "2023-10-20T14:32:32.561661+00:00",
                        "inputEvent": None,
                        "outputEvent": {
                            "currentStageName": "Label",
                            "outputBool": None,
                        },
                        "createEvent": None,
                        "taskData": {
                            "stageName": "Label",
                            "createdBy": "1c643889-5a8b-4b20-8e48-14e9cbd5eeb7",
                        },
                    },
                    {
                        "__typename": "TaskEvent",
                        "eventId": "6d8cfc43-16c6-4428-a10a-ab12900da6fd",
                        "createdAt": "2023-10-20T14:32:33.049407+00:00",
                        "inputEvent": {
                            "currentStageName": "Review_1",
                            "overallConsensusScore": None,
                        },
                        "outputEvent": None,
                        "createEvent": None,
                        "taskData": {
                            "stageName": "Review_1",
                            "createdBy": "1c643889-5a8b-4b20-8e48-14e9cbd5eeb7",
                        },
                    },
                    {
                        "__typename": "TaskStateChanges",
                        "stageNameAfter": "Review_1",
                        "assignedAtAfter": "2023-10-20T14:32:48.427416+00:00",
                        "createdAt": "2023-10-20T14:32:48.469884+00:00",
                        "statusBefore": "UNASSIGNED",
                        "statusAfter": "ASSIGNED",
                        "assignedToBefore": None,
                        "assignedToAfter": "1c643889-5a8b-4b20-8e48-14e9cbd5eeb7",
                        "consensusAssigneesBefore": [],
                        "consensusAssigneesAfter": [],
                        "consensusStatusesBefore": [],
                        "consensusStatusesAfter": [],
                    },
                    {
                        "__typename": "TaskStateChanges",
                        "stageNameAfter": "Review_1",
                        "assignedAtAfter": "2023-10-20T14:32:53.350676+00:00",
                        "createdAt": "2023-10-20T14:33:01.540533+00:00",
                        "statusBefore": "ASSIGNED",
                        "statusAfter": "COMPLETED",
                        "assignedToBefore": "1c643889-5a8b-4b20-8e48-14e9cbd5eeb7",
                        "assignedToAfter": "1c643889-5a8b-4b20-8e48-14e9cbd5eeb7",
                        "consensusAssigneesBefore": [],
                        "consensusAssigneesAfter": [],
                        "consensusStatusesBefore": [],
                        "consensusStatusesAfter": [],
                    },
                    {
                        "__typename": "TaskEvent",
                        "eventId": "b63041fa-3c0e-45f2-ae9b-a26f76ef860d",
                        "createdAt": "2023-10-20T14:33:01.616242+00:00",
                        "inputEvent": None,
                        "outputEvent": {
                            "currentStageName": "Review_1",
                            "outputBool": True,
                        },
                        "createEvent": None,
                        "taskData": {
                            "stageName": "Review_1",
                            "createdBy": "1c643889-5a8b-4b20-8e48-14e9cbd5eeb7",
                        },
                    },
                    {
                        "__typename": "TaskEvent",
                        "eventId": "cff7487c-a3fd-4261-b8e2-cdd32579b43b",
                        "createdAt": "2023-10-20T14:33:02.059907+00:00",
                        "inputEvent": {
                            "currentStageName": "Output",
                            "overallConsensusScore": None,
                        },
                        "outputEvent": None,
                        "createEvent": None,
                        "taskData": {
                            "stageName": "Output",
                            "createdBy": "1c643889-5a8b-4b20-8e48-14e9cbd5eeb7",
                        },
                    },
                    {
                        "__typename": "TaskEvent",
                        "eventId": "c6ccb3ba-86d1-46a3-af34-2b475ab2d14f",
                        "createdAt": "2023-10-20T14:33:02.392030+00:00",
                        "inputEvent": None,
                        "outputEvent": {
                            "currentStageName": "Output",
                            "outputBool": None,
                        },
                        "createEvent": None,
                        "taskData": {
                            "stageName": "Output",
                            "createdBy": "1c643889-5a8b-4b20-8e48-14e9cbd5eeb7",
                        },
                    },
                ],
            },
        ],
        "cursor": None,
    }
}


def active_time_resp(mock_task_id: str):
    """Mock response for `ExportRepo.active_time`"""
    resp = {
        "taskActiveTime": {
            "cursor": None,
            "entries": [
                {
                    "cycle": 0,
                    "date": "2023-10-20T14:33:27.931070+00:00",
                    "taskId": mock_task_id,
                    "timeSpent": 10254,
                    "user": {"userId": "1c643889-5a8b-4b20-8e48-14e9cbd5eeb7"},
                }
            ],
        }
    }
    return resp


# pylint: enable=pointless-string-statement
# pylint: enable=line-too-long
