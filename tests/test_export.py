"""Tests for redbrick.mock_export.public"""
import os
import typing as t
from unittest.mock import patch, Mock, AsyncMock, MagicMock, mock_open

import pytest

import redbrick.export
from tests.fixtures import export as export_fixtures, repo as repo_fixtures


@pytest.mark.unit
def test_get_raw_data_latest(mock_export):
    """Test `redbrick.export.public.Export._get_raw_data_latest`"""
    mock_task_id = "mock_task_id"
    concurrency = 2

    mock_query = Mock(
        return_value=repo_fixtures.get_datapoint_latest_resp(mock_task_id)
    )
    mock_export.context.export.client.execute_query = mock_query
    resp = mock_export._get_raw_data_latest(  # pylint: disable=protected-access
        concurrency, task_id=mock_task_id
    )

    tasks = list(resp)
    assert len(tasks) == 1
    assert tasks[0]["taskId"] == mock_task_id


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.parametrize(
    ("rt_struct", "taxonomy", "check_convert_called"),
    [
        (True, {"taxonomy": []}, False),
        (False, {"isNew": True, "objectTypes": []}, False),
        (True, {"isNew": True, "objectTypes": []}, True),
    ],
)
async def test_download_task_items(
    mock_export, rt_struct, taxonomy, check_convert_called, tmpdir
):
    """Test `redbrick.export.public.Export._download_task_items`"""
    task = export_fixtures.get_tasks_resp[2]
    storage_id = "storage_id"
    parent_dir = str(tmpdir)

    async def mock_download(
        url_path_pairs: t.List[t.Tuple[str, str]], *args
    ):  # pylint: disable=unused-argument
        return [x[1] for x in url_path_pairs]

    mock_convert = AsyncMock(return_value=None)
    mock_export.context.export.presign_items = lambda a, b, items: items
    with patch("redbrick.export.public.download_files", mock_download):
        with patch("redbrick.utils.dicom.convert_nii_to_rtstruct", mock_convert):
            (
                _,
                series_dirs,
            ) = await mock_export._download_task_items(  # pylint: disable=protected-access
                task, storage_id, parent_dir, taxonomy, rt_struct
            )
    if check_convert_called:
        mock_convert.assert_called_once()
    assert series_dirs == [
        os.path.join(parent_dir, "BraTS2021_00005", "A"),
        os.path.join(parent_dir, "BraTS2021_00005", "B"),
        os.path.join(parent_dir, "BraTS2021_00005", "C"),
        os.path.join(parent_dir, "BraTS2021_00005", "D"),
    ]
    assert len(series_dirs) == len(task["series"])


@pytest.mark.unit
@pytest.mark.parametrize("get_color_map", [False, True])
def test_preprocess_export(mock_export, get_color_map):
    """Test `redbrick.export.public.Export.preprocess_export`"""
    taxonomy = {
        "isNew": True,
        "objectTypes": [
            {
                "labelType": "SEGMENTATION",
                "classId": "class1",
                "color": "FF0000",
                "category": "Category1",
            }
        ],
    }
    class_map, color_map = mock_export.preprocess_export(
        taxonomy, get_color_map=get_color_map
    )
    if get_color_map:
        assert class_map == {"Category1": [255, 0, 0]}
        assert color_map == {"class1": [255, 0, 0]}
    else:
        assert class_map == color_map == {}


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("task_file", "get_task", "returns_task"),
    [
        (None, False, False),
        (None, True, True),
        ("/tmp/taskfile", True, True),
    ],
)
async def test_export_nifti_label_data(mock_export, task_file, get_task, returns_task):
    """Test `redbrick.export.public.Export.export_nifti_label_data`"""
    # Mock methods
    async def mock_download_task(_task, *args):  # pylint: disable=unused-argument
        return _task

    mock_export._download_task = mock_download_task  # pylint: disable=protected-access
    mock_export.process_labels = AsyncMock(
        return_value=export_fixtures.get_tasks_resp[2]
    )

    datapoint = {
        "labelStorageId": "storage123",
        "labels": ["Label", "Review_1", "END"],
        "items": [],
    }

    taxonomy = {
        "isNew": True,
        "objectTypes": [
            {
                "labelType": "SEGMENTATION",
                "classId": "class1",
                "color": "FF0000",
                "category": "Category1",
            }
        ],
    }
    open_mock = MagicMock(spec=open)
    with patch.object(redbrick.export.public, "open", mock_open(mock=open_mock)):
        task = await mock_export.export_nifti_label_data(
            datapoint,
            taxonomy,
            task_file,
            None,
            None,
            False,
            None,
            False,
            False,
            False,
            False,
            False,
            False,
            get_task,
        )
    mock_export.process_labels.assert_called_once()
    if task_file:
        open_mock.assert_called_once()

    if returns_task:
        assert isinstance(task, dict)
    else:
        assert task is None


@pytest.mark.unit
def test_export_tasks(mock_export, tmpdir):
    """Test `redbrick.export.public.Export.export_tasks`"""
    # Mock the _get_raw_data_latest method
    taxonomy = {
        "isNew": True,
        "objectTypes": [
            {
                "labelType": "SEGMENTATION",
                "classId": "class1",
                "color": "FF0000",
                "category": "Category1",
            }
        ],
    }
    class_map = {"Category1": [255, 0, 0]}
    color_map = {"class1": [255, 0, 0]}
    task_id_to_tasks = {x["taskId"]: x for x in export_fixtures.get_tasks_resp}
    destination_dir = str(tmpdir)

    # patch methods
    mock_export.context.project.get_taxonomy = MagicMock(return_value=taxonomy)
    mock_export.preprocess_export = MagicMock(return_value=(class_map, color_map))
    # patch "self.context.export.get_datapoints_latest" and
    # by extension, "_get_raw_data_latest"
    mock_query = Mock(return_value=repo_fixtures.get_datapoints_latest_resp)
    mock_export.context.export.client.execute_query = mock_query

    async def _mock_nifti(datapoint, *args):  # pylint: disable=unused-argument
        return task_id_to_tasks[datapoint["taskId"]]

    mock_export.export_nifti_label_data = _mock_nifti

    # Mock with_files=True and test
    task_ids = set()
    for task_ in mock_export.export_tasks(destination=destination_dir):
        assert isinstance(task_, dict)
        task_ids.add(task_["taskId"])
    assert task_ids == set(task_id_to_tasks)

    # Mock rt_struct=True and test
    mock_makedirs = MagicMock()
    open_mock = MagicMock(spec=open)
    with patch.object(redbrick.export.public, "open", mock_open(mock=open_mock)):
        with patch.object(redbrick.export.public.os, "makedirs", mock_makedirs):
            task_ = next(
                mock_export.export_tasks(
                    rt_struct=True,
                    with_files=True,
                    without_json=False,
                    without_masks=False,
                    png=True,
                    destination=destination_dir,
                )
            )
    open_mock.assert_called_once()
    assert mock_makedirs.call_count == 2
    assert task_["taskId"] in task_id_to_tasks


@pytest.mark.unit
@pytest.mark.parametrize(
    ("kwargs", "expected_filters", "expected_stage_name"),
    [
        ({"user_id": "mock"}, {"userId"}, "Label"),
        ({"task_id": "mock", "user_id": "mock"}, {"userId", "taskId"}, "Label"),
        ({"user_id": "mock", "search": "ALL"}, {}, None),
        ({"user_id": "mock", "search": "GROUNDTRUTH"}, {}, "END"),
        ({"search": "QUEUED"}, {}, "Label"),
        ({"search": "DRAFT"}, {"status"}, "Label"),
        ({"search": "SKIPPED"}, {"status"}, "Label"),
        ({"search": "COMPLETED"}, {"recentlyCompleted"}, "Label"),
        ({"search": "FAILED", "user_id": "mock"}, {"reviewState"}, "Review_1"),
        ({"search": "ISSUES", "user_id": "mock"}, {"status"}, "Label"),
        ({"search": "BENCHMARK", "user_id": "mock"}, {"benchmark"}, "END"),
        ({"search": "InvalidFilter"}, None, "Label"),
    ],
)
def test_list_tasks(
    mock_export,
    kwargs: t.Dict,
    expected_filters: t.Optional[t.Set],
    expected_stage_name: t.Optional[str],
):
    """
    Test `redbrick.export.public.Export.list_tasks`
    Ensure the right filters gets passed to the Repo method
    """
    # Simulate a call to list_tasks with some parameters
    _tasks = repo_fixtures.task_search_resp("Label")["genericTasks"]["entries"]
    mock_export.context.export.task_search = MagicMock(return_value=(_tasks, None))
    mock_export.context.project.get_members = MagicMock(return_value={})

    search = kwargs.pop("search", "QUEUED")

    if expected_filters is None:
        with pytest.raises(ValueError):
            next(
                mock_export.list_tasks(
                    search=search, limit=10, stage_name="Label", **kwargs
                )
            )
        return

    task = next(
        mock_export.list_tasks(search=search, limit=10, stage_name="Label", **kwargs)
    )

    calls = mock_export.context.export.task_search.mock_calls
    call_args = calls[0].args
    stage_name_ = call_args[2]
    filters = call_args[4]

    assert set(filters) == set(expected_filters)
    assert isinstance(task, dict)
    assert isinstance(task.get("taskId"), str)
    assert stage_name_ == expected_stage_name
