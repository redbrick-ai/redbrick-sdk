"""Fixtures for tests in `tests.test_export.py`"""
import typing as t


# pylint: disable=line-too-long
# mock Task object
get_tasks_resp: t.List[t.Dict] = [
    {
        "createdAt": "2023-10-20T14:31:38.610645+00:00",
        "createdBy": "mock@email.com",
        "currentStageName": "Label",
        "name": "BraTS2021_00003",
        "series": [
            {
                "items": [
                    "https://mock.com/some_randon_image/BraTS2021_00003/BraTS2021_00003_t2.nii.gz"
                ]
            },
            {
                "items": [
                    "https://mock.com/some_randon_image/BraTS2021_00003/BraTS2021_00003_t1ce.nii.gz"
                ]
            },
            {
                "items": [
                    "https://mock.com/some_randon_image/BraTS2021_00003/BraTS2021_00003_t1.nii.gz"
                ]
            },
            {
                "items": [
                    "https://mock.com/some_randon_image/BraTS2021_00003/BraTS2021_00003_flair.nii.gz"
                ]
            },
        ],
        "taskId": "af454bb5-9fc8-4b22-a2b9-033d49e28539",
        "updatedAt": "2023-10-20T14:31:38.610700+00:00",
        "updatedBy": "mock@email.com",
    },
    {
        "createdAt": "2023-10-20T14:31:38.610819+00:00",
        "createdBy": "mock@email.com",
        "currentStageName": "Label",
        "name": "BraTS2021_00009",
        "series": [
            {
                "items": [
                    "https://mock.com/some_randon_image/BraTS2021_00009/BraTS2021_00009_t2.nii.gz",
                    "https://mock.com/some_randon_image/BraTS2021_00009/BraTS2021_00009_t1ce.nii.gz",
                    "https://mock.com/some_randon_image/BraTS2021_00009/BraTS2021_00009_flair.nii.gz",
                    "https://mock.com/some_randon_image/BraTS2021_00009/BraTS2021_00009_t1.nii.gz",
                ]
            }
        ],
        "taskId": "682c8185-1e9d-4c49-b98d-869971c9304a",
        "updatedAt": "2023-10-20T14:31:38.610835+00:00",
        "updatedBy": "mock@email.com",
    },
    {
        "classification": {},
        "createdAt": "2023-10-20T14:31:38.610727+00:00",
        "createdBy": "derek+chima@redbrickai.com",
        "currentStageName": "END",
        "name": "BraTS2021_00005",
        "series": [
            {
                "binaryMask": False,
                "items": [
                    "https://datasets.redbrickai.com/brain-brats/NIFTI_images/BraTS2021_00005/BraTS2021_00005_t1ce.nii.gz",
                    "https://datasets.redbrickai.com/brain-brats/NIFTI_images/BraTS2021_00005/BraTS2021_00005_t2ce.nii.gz",
                ],
                "pngMask": False,
                "segmentMap": {
                    "1": {
                        "category": "liver",
                        "mask": "./segmentations/BraTS2021_00005/A.nii.gz",
                    }
                },
                "segmentations": "./segmentations/BraTS2021_00005/A.nii.gz",
                "semanticMask": False,
            },
            {
                "binaryMask": False,
                "items": [
                    "https://datasets.redbrickai.com/brain-brats/NIFTI_images/BraTS2021_00005/BraTS2021_00005_t2.nii.gz"
                ],
                "pngMask": False,
                "segmentMap": {
                    "1": {
                        "category": "lung",
                        "mask": "./segmentations/BraTS2021_00005/B.nii.gz",
                    }
                },
                "segmentations": "./segmentations/BraTS2021_00005/B.nii.gz",
                "semanticMask": False,
            },
            {
                "binaryMask": False,
                "items": [
                    "https://datasets.redbrickai.com/brain-brats/NIFTI_images/BraTS2021_00005/BraTS2021_00005_flair.nii.gz"
                ],
                "pngMask": False,
                "segmentMap": {
                    "1": {
                        "category": "kidney",
                        "mask": "./segmentations/BraTS2021_00005/C.nii.gz",
                    }
                },
                "segmentations": "./segmentations/BraTS2021_00005/C.nii.gz",
                "semanticMask": False,
            },
            {
                "items": [
                    "https://datasets.redbrickai.com/brain-brats/NIFTI_images/BraTS2021_00005/BraTS2021_00005_t1.nii.gz"
                ]
            },
        ],
        "taskId": "2067f35a-90e6-4243-965d-8d64868021bd",
        "updatedAt": "2023-10-20T14:32:32.204050+00:00",
        "updatedBy": "derek+chima@redbrickai.com",
    },
    {
        "classification": {},
        "createdAt": "2023-10-20T14:31:38.610885+00:00",
        "createdBy": "derek+chima@redbrickai.com",
        "currentStageName": "Review_1",
        "name": "BraTS2021_00006",
        "series": [
            {
                "binaryMask": False,
                "items": [
                    "https://datasets.redbrickai.com/brain-brats/NIFTI_images/BraTS2021_00006/BraTS2021_00006_t1.nii.gz"
                ],
                "pngMask": False,
                "segmentMap": {
                    "1": {
                        "category": "liver",
                        "mask": "./segmentations/BraTS2021_00006/A.nii.gz",
                    }
                },
                "segmentations": "./segmentations/BraTS2021_00006/A.nii.gz",
                "semanticMask": False,
            },
            {
                "items": [
                    "https://datasets.redbrickai.com/brain-brats/NIFTI_images/BraTS2021_00006/BraTS2021_00006_flair.nii.gz"
                ]
            },
            {
                "items": [
                    "https://datasets.redbrickai.com/brain-brats/NIFTI_images/BraTS2021_00006/BraTS2021_00006_t1ce.nii.gz"
                ]
            },
            {
                "binaryMask": False,
                "items": [
                    "https://datasets.redbrickai.com/brain-brats/NIFTI_images/BraTS2021_00006/BraTS2021_00006_t2.nii.gz"
                ],
                "pngMask": False,
                "segmentMap": {
                    "1": {
                        "category": "lung",
                        "mask": "./segmentations/BraTS2021_00006/D.nii.gz",
                    }
                },
                "segmentations": "./segmentations/BraTS2021_00006/D.nii.gz",
                "semanticMask": False,
            },
        ],
        "taskId": "6a12cb11-ce37-43a1-b8b6-20b1317afffd",
        "updatedAt": "2023-10-20T14:33:27.664115+00:00",
        "updatedBy": "derek+chima@redbrickai.com",
    },
]
# pylint: enable=line-too-long
