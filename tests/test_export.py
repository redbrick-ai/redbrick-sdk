"""Tests for redbrick.mock_export.public"""
import io
import typing as t
from unittest.mock import patch, Mock, AsyncMock, MagicMock, mock_open

import pytest

from redbrick.export import Export
from tests.fixtures import export as export_fixtures
from tests.test_repo import conftest as repo_conftest


def test_get_raw_data_latest(mock_export):
    mock_task_id = "mock_task_id"
    concurrency = 2

    mock_query = Mock(
        return_value=repo_conftest.get_datapoint_latest_resp(mock_task_id)
    )
    mock_export.context.export.client.execute_query = mock_query
    resp = mock_export._get_raw_data_latest(concurrency, task_id=mock_task_id)

    tasks = list(resp)
    assert len(tasks) == 1
    assert tasks[0]["taskId"] == mock_task_id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("rt_struct", "taxonomy", "check_convert_called"),
    [
        (True, {"taxonomy": []}, False),
        (False, {"isNew": True, "objectTypes": []}, False),
        (True, {"isNew": True, "objectTypes": []}, True),
    ]
)
async def test_download_task_items(mock_export, rt_struct, taxonomy, check_convert_called):
    task = export_fixtures.get_tasks()[2]
    storage_id = "storage_id"
    parent_dir = "parent_dir"

    async def mock_download(url_path_pairs: t.List[t.Tuple[str, str]], *args):
        return [x[1] for x in url_path_pairs]

    mock_convert = AsyncMock(return_value=None)
    mock_export.context.export.presign_items = lambda a, b, items: items
    with patch("redbrick.export.public.download_files", mock_download):
        with patch("redbrick.utils.dicom.convert_nii_to_rtstruct", mock_convert):
            task_, series_dirs = await mock_export._download_task_items(
                task, storage_id, parent_dir, taxonomy, rt_struct
            )
    if check_convert_called:
        mock_convert.assert_called_once()
    assert series_dirs == ['parent_dir/BraTS2021_00005/A', 'parent_dir/BraTS2021_00005/B', 'parent_dir/BraTS2021_00005/C', 'parent_dir/BraTS2021_00005/D']
    assert len(task["series"]) == len(series_dirs)


@pytest.mark.parametrize("get_color_map", [False, True])
def test_preprocess_export(mock_export, get_color_map):
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
    class_map, color_map = mock_export.preprocess_export(taxonomy, get_color_map=get_color_map)
    if get_color_map:
        assert class_map == {"Category1": [255, 0, 0]}
        assert color_map == {"class1": [255, 0, 0]}
    else:
        assert class_map == color_map == {}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("task_file", "get_task", "returns_task"),
    [
        (None, False, False),
        (None, True, True),
        ("/tmp/taskfile", True, True),
    ]
)
async def test_export_nifti_label_data(mock_export, task_file, get_task, returns_task):
    # Mock methods
    async def mock_download_task(_task, *args):
        return _task

    mock_export._download_task = mock_download_task
    tasks = export_fixtures.get_tasks()
    mock_export.process_labels = AsyncMock(return_value=tasks[2])

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
    import redbrick.export
    with patch.object(redbrick.export.public, "open", mock_open(mock=open_mock)):
        with io.BytesIO() as mock_file:
            task = await mock_export.export_nifti_label_data(
                datapoint, taxonomy, task_file, None, None, False, None, False, False, False, False, False, False, get_task
            )
    mock_export.process_labels.assert_called_once()
    if task_file:
        open_mock.assert_called_once()

    if returns_task:
        assert isinstance(task, dict)
    else:
        assert task is None
