"""Tests for `redbrick.utils.rb_label_utils`."""
import pytest

from redbrick.utils import rb_label_utils
from tests.fixtures import repo as repo_fixtures


@pytest.mark.unit
def test_clean_rb_label():
    """Test clean_rb_label function"""
    input_label = {"key1": "value1", "key2": None, "key3": "value3"}
    expected_result = {"key1": "value1", "key3": "value3"}
    assert rb_label_utils.clean_rb_label(input_label) == expected_result


@pytest.mark.unit
def test_user_format():
    """Test  rb_label_utils.user_format function"""
    users = {"RB:123": "System", "API:456": "API Key", "user123": "User123"}
    assert rb_label_utils.user_format("RB:123", users) == "System"
    assert rb_label_utils.user_format("API:456", users) == "API Key"
    assert rb_label_utils.user_format("user123", users) == "User123"
    assert rb_label_utils.user_format("unknown_user", users) == "unknown_user"


@pytest.mark.unit
def test_from_rb_task_data():
    """Test rb_label_utils.from_rb_task_data function"""
    task_data = {
        "createdAt": "2023-10-26T12:34:56",
        "labelsData": '[{"label1": "value1"}, {"label2": "value2"}]',
        "labelsMap": [{"label1": "map1"}, {"label2": "map2"}],
        "labelsStorage": {"storageId": "storage123"},
    }
    expected_result = {
        "updatedAt": "2023-10-26T12:34:56",
        "labels": [{"label1": "value1"}, {"label2": "value2"}],
        "labelsMap": [{"label1": "map1"}, {"label2": "map2"}],
        "labelStorageId": "storage123",
    }
    result = rb_label_utils.from_rb_task_data(task_data)
    assert result == expected_result


@pytest.mark.unit
def test_from_rb_sub_task():
    """Test rb_label_utils.from_rb_sub_task function"""
    sub_task = {
        "assignedTo": {"userId": "user123", "email": "user@example.com"},
        "state": "completed",
        "taskData": {
            "createdAt": "2023-10-26T12:34:56",
            "labelsData": '[{"label1": "value1"}, {"label2": "value2"}]',
            "labelsMap": [{"label1": "map1"}, {"label2": "map2"}],
            "labelsStorage": {"storageId": "storage123"},
        },
    }
    expected_result = {
        "status": "completed",
        "assignee": "user@example.com",
        "updatedAt": "2023-10-26T12:34:56",
        "labels": [{"label1": "value1"}, {"label2": "value2"}],
        "labelsMap": [{"label1": "map1"}, {"label2": "map2"}],
        "labelStorageId": "storage123",
    }
    result = rb_label_utils.from_rb_sub_task(sub_task)
    assert result == expected_result


@pytest.mark.unit
def test_from_rb_consensus_info():
    """Test rb_label_utils.from_rb_consensus_info function"""
    # pylint: disable=line-too-long
    datapoint = repo_fixtures.get_datapoints_latest_resp["tasksPaged"]["entries"][2]
    consensus_info = datapoint["currentStageSubTask"]["consensusInfo"][0]
    expected_result = {
        "assignee": "API Key",
        "updatedAt": "2023-10-20T14:33:27.664115+00:00",
        "labels": [
            {
                "category": "liver",
                "attributes": [],
                "classid": 0,
                "labelid": "7f138361-dad9-4a90-853a-cf030a605221",
                "dicom": {"instanceid": 1, "groupids": None},
                "volumeindex": 0,
            },
            {
                "category": "lung",
                "attributes": [],
                "classid": 1,
                "labelid": "302a87fc-eabd-402e-a95e-9c32529d2901",
                "dicom": {"instanceid": 1, "groupids": None},
                "volumeindex": 3,
            },
            {
                "attributes": [],
                "labelid": "d775111e-7a47-445e-9f46-dd84cd64b8ba",
                "studyclassify": True,
            },
        ],
        "labelsMap": [
            {
                "imageIndex": 0,
                "labelName": "c78d312f-5b41-4b66-9c06-44c375abe057/75a0af6f-4f48-46dd-a4d2-1b43ea238559/labels/6a12cb11-ce37-43a1-b8b6-20b1317afffd/nifti/80feaafb-2456-48fb-833f-2012138a63e7",  # noqa
            },
            {
                "imageIndex": 3,
                "labelName": "c78d312f-5b41-4b66-9c06-44c375abe057/75a0af6f-4f48-46dd-a4d2-1b43ea238559/labels/6a12cb11-ce37-43a1-b8b6-20b1317afffd/nifti/73d5388a-d742-43c9-950e-29fc116527e7",  # noqa
            },
        ],
        "labelStorageId": "22222222-2222-2222-2222-222222222222",
        "scores": [],
    }
    result = rb_label_utils.from_rb_consensus_info(consensus_info)
    assert result == expected_result


@pytest.mark.unit
def test_flat_rb_format():
    """Test rb_label_utils.flat_rb_format function"""
    # pylint: disable=too-many-locals
    labels = [{"label1": "value1"}, {"label2": "value2"}]
    items = ["item1", "item2"]
    name = "Task Name"
    created_by = "user123"
    created_at = "2023-10-26T12:34:56"
    updated_by = "user456"
    updated_at = "2023-10-26T12:45:00"
    task_id = "task123"
    current_stage_name = "Stage1"
    priority = 1.0
    labels_map = [{"label3": "map3"}, {"label4": "map4"}]
    series_info = [{"name": "Series1"}, {"name": "Series2"}]
    meta_data = {"key": "value"}
    storage_id = "storage123"
    label_storage_id = "labelStorage123"
    current_stage_sub_task = {
        "subTasks": [
            {"assignedTo": {"userId": "user789", "email": "user789@example.com"}},
            {"assignedTo": {"userId": "user101", "email": "user101@example.com"}},
        ]
    }
    expected_result = {
        "consensusTasks": [
            {
                "assignee": None,
                "labelStorageId": None,
                "labels": [],
                "labelsMap": [],
                "status": None,
                "updatedAt": None,
            },
            {
                "assignee": "user789@example.com",
                "labelStorageId": None,
                "labels": [],
                "labelsMap": [],
                "status": None,
                "updatedAt": None,
            },
            {
                "assignee": "user101@example.com",
                "labelStorageId": None,
                "labels": [],
                "labelsMap": [],
                "status": None,
                "updatedAt": None,
            },
        ],
        "createdAt": "2023-10-26T12:34:56",
        "createdBy": "user123",
        "currentStageName": "Stage1",
        "items": ["item1", "item2"],
        "itemsPresigned": ["item1", "item2"],
        "labelStorageId": "labelStorage123",
        "labels": [{"label1": "value1"}, {"label2": "value2"}],
        "labelsMap": [{"label3": "map3"}, {"label4": "map4"}],
        "metaData": {"key": "value"},
        "name": "Task Name",
        "priority": 1.0,
        "seriesInfo": [{"name": "Series1"}, {"name": "Series2"}],
        "storageId": "storage123",
        "taskId": "task123",
        "updatedAt": "2023-10-26T12:45:00",
        "updatedBy": "user456",
    }

    result = rb_label_utils.flat_rb_format(
        labels,
        items,
        items,
        name,
        created_by,
        created_at,
        updated_by,
        updated_at,
        task_id,
        current_stage_name,
        priority,
        labels_map,
        series_info,
        meta_data,
        storage_id,
        label_storage_id,
        current_stage_sub_task,
    )
    assert result == expected_result


@pytest.mark.unit
def test_parse_entry_latest():
    """Test rb_label_utils.parse_entry_latest function"""
    # pylint: disable=line-too-long
    entry = repo_fixtures.get_datapoints_latest_resp["tasksPaged"]["entries"][2]

    result = rb_label_utils.parse_entry_latest(entry)
    expected = {
        "taskId": "6a12cb11-ce37-43a1-b8b6-20b1317afffd",
        "name": "BraTS2021_00006",
        "items": [
            "https://mock.com/some_randon_image/BraTS2021_00006/BraTS2021_00006_t1.nii.gz",
            "https://mock.com/some_randon_image/BraTS2021_00006/BraTS2021_00006_flair.nii.gz",
            "https://mock.com/some_randon_image/BraTS2021_00006/BraTS2021_00006_t1ce.nii.gz",
            "https://mock.com/some_randon_image/BraTS2021_00006/BraTS2021_00006_t2.nii.gz",
        ],
        "itemsPresigned": [],
        "currentStageName": "Review_1",
        "createdBy": "mock@email.com",
        "createdAt": "2023-10-20T14:31:38.610885+00:00",
        "updatedBy": "mock@email.com",
        "updatedAt": "2023-10-20T14:33:27.664115+00:00",
        "labels": [
            {
                "category": "liver",
                "attributes": [],
                "classid": 0,
                "labelid": "7f138361-dad9-4a90-853a-cf030a605221",
                "dicom": {"instanceid": 1, "groupids": None},
                "volumeindex": 0,
            },
            {
                "category": "lung",
                "attributes": [],
                "classid": 1,
                "labelid": "302a87fc-eabd-402e-a95e-9c32529d2901",
                "dicom": {"instanceid": 1, "groupids": None},
                "volumeindex": 3,
            },
            {
                "attributes": [],
                "labelid": "d775111e-7a47-445e-9f46-dd84cd64b8ba",
                "studyclassify": True,
            },
        ],
        "labelsMap": [
            {
                "imageIndex": 0,
                "labelName": "c78d312f-5b41-4b66-9c06-44c375abe057/75a0af6f-4f48-46dd-a4d2-1b43ea238559/labels/6a12cb11-ce37-43a1-b8b6-20b1317afffd/nifti/80feaafb-2456-48fb-833f-2012138a63e7",  # noqa
            },
            {
                "imageIndex": 3,
                "labelName": "c78d312f-5b41-4b66-9c06-44c375abe057/75a0af6f-4f48-46dd-a4d2-1b43ea238559/labels/6a12cb11-ce37-43a1-b8b6-20b1317afffd/nifti/73d5388a-d742-43c9-950e-29fc116527e7",  # noqa
            },
        ],
        "seriesInfo": [
            {"name": None, "itemsIndices": [0], "dataType": "nifti", "metaData": None},
            {"name": None, "itemsIndices": [1], "dataType": "nifti", "metaData": None},
            {"name": None, "itemsIndices": [2], "dataType": "nifti", "metaData": None},
            {"name": None, "itemsIndices": [3], "dataType": "nifti", "metaData": None},
        ],
        "metaData": None,
        "storageId": "11111111-1111-1111-1111-111111111111",
        "labelStorageId": "22222222-2222-2222-2222-222222222222",
        "priority": None,
    }
    assert result == expected


@pytest.mark.unit
def test_dicom_rb_series(mock_labels):
    """Test dicom_rb_series function"""
    item_index_map = {}
    input_task = {
        "labels": mock_labels,
        "items": ["Item 1", "Item 2", "Item 3"],
        "labelsMap": [
            {
                "labelName": "Review",
                "binaryMask": True,
                "semanticMask": True,
                "pngMask": True,
            }
        ],
        "series": [{}],
    }
    output_task = {"series": [{}], "seriesInfo": [{"itemsIndices": [0, 1]}]}
    taxonomy = {"isNew": True}

    rb_label_utils.dicom_rb_series(item_index_map, input_task, output_task, taxonomy)

    series = output_task["series"][0]
    expected_keys = {
        "binaryMask",
        "pngMask",
        "semanticMask",
        "segmentMap",
        "segmentations",
    }
    assert set(series) == expected_keys
    assert len(series["segmentMap"]) == 3
    assert all([series[k]] for k in ["binaryMask", "semanticMask", "pngMask"])


@pytest.mark.unit
def test_dicom_rb_format():
    """Test dicom_rb_format function"""
    # Create a sample task and taxonomy
    task = {
        "taskId": "123",
        "name": "Sample Task",
        "currentStageName": "Review_1",
        "priority": 1.0,
        "createdBy": "John",
        "createdAt": "2023-01-01",
        "labels": [],
        "labelsMap": [],
        "items": ["mock1", "mock2", "mock3"],
        "seriesInfo": [{"itemsIndices": [0, 1, 2]}],
        "consensusScore": 80,
        "consensusTasks": [
            {
                "assignee": {},
                "status": "mock",
                "email": "mock@email.com",
                "userId": "mock",
                "updatedAt": "2023-10-20T14:33:27.664115+00:00",
                "scores": [
                    {
                        "userId": "mock",
                        "email": "mock@email.com",
                        "score": 100,
                    }
                ],
            }
        ],
    }
    taxonomy = {"isNew": True}

    result = rb_label_utils.dicom_rb_format(task, taxonomy, False, False, [])
    assert result["taskId"] == "123"
    assert result["name"] == "Sample Task"
    assert result["currentStageName"] == "Review_1"
    assert result["priority"] == 1.0
    assert result["createdBy"] == "John"
    assert result["createdAt"] == "2023-01-01"
    assert "consensusScore" in result
