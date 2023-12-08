"""Tests for `redbrick.cli.command.export`."""
import argparse
import json
import os
from datetime import datetime
from unittest.mock import patch, Mock

import pytest

from redbrick.cli import public, CLIProject
from redbrick.cli.command import CLIExportController


@pytest.mark.unit
def test_handler(prepare_project, monkeypatch):
    """Test `CLIUploadController.handler` correctly gets project details"""
    project_path, config_path_, _, _ = prepare_project
    monkeypatch.chdir(project_path)
    _, cli = public.cli_parser(only_parser=False)

    with patch(
        "redbrick.cli.project.config_path", return_value=config_path_
    ), patch.object(cli.export, "handle_export") as _handle_export:
        args = argparse.Namespace(command=cli.EXPORT, path=project_path)
        cli.export.handler(args)
        _handle_export.assert_called_once()
        assert isinstance(cli.export.project, CLIProject)


@pytest.mark.unit
@pytest.mark.parametrize("new_tax", [True, False])
def test_handle_export(
    mock_export_controller, monkeypatch, new_tax
):  # pylint: disable=too-many-locals
    """Test the `CLIUploadController.handle_upload` with different
    values of the "new_tax" argument
    """
    controller: CLIExportController
    controller, project_path = mock_export_controller
    monkeypatch.chdir(project_path)

    # pylint: disable=unused-argument
    mock_taxonomy_new = {
        "isNew": True,
        "objectTypes": [
            {
                "labelType": "SEGMENTATION",
                "category": "mock_category",
                "classId": 0,
                "color": "#B48950",
            },
        ],
    }
    mock_taxonomy_old = {
        "categories": [
            {
                "name": "mock_tax_catg",
                "children": [
                    {
                        "name": "mock_inner_tax_catg",
                        "classId": 0,
                        "children": {},
                    }
                ],
            },
        ],
        "colorMap": [{"trail": "mock_inner_tax_catg"}],
    }
    mock_datapoint = {
        "taskId": "mock_task_id",
        "latestTaskData": {
            "dataPoint": {
                "items": ["https://some-random-url.com/some/randon/file.nii.gz"],
                "itemsPresigned": [],
                "name": "mock_dp",
                "createdAt": "2023-10-20T14:31:38.610700+00:00",
                "createdByEntity": {"email": "mock@email.com"},
                "storageMethod": {"storageId": "11111111-1111-1111-1111-111111111111"},
                "seriesInfo": [
                    {
                        "dataType": "nifti",
                        "itemsIndices": [0],
                        "metaData": None,
                        "name": None,
                    },
                ],
                "metaData": json.dumps({}),
            },
            "createdAt": "2023-10-20T14:31:38.610700+00:00",
            "createdByEmail": "mock@email.com",
            "labelsData": json.dumps([]),
            "labelsStorage": {"storageId": "22222222-2222-2222-2222-222222222222"},
            "labelsMap": None,
        },
        "currentStageName": "Label",
        "priority": None,
        "currentStageSubTask": {},
    }
    mock_taxonomy = mock_taxonomy_new if new_tax else mock_taxonomy_old
    mock_get_taxonomy = Mock(return_value=mock_taxonomy)

    mock_datapoints_in_project = Mock(return_value=1)
    mock_get_datapoints_latest = Mock(return_value=([mock_datapoint], None, None))
    # pylint: enable=unused-argument

    with patch.object(
        controller.project.project.context.project, "get_taxonomy", mock_get_taxonomy
    ), patch.object(
        controller.project.project.context.export,
        "datapoints_in_project",
        mock_datapoints_in_project,
    ), patch.object(
        controller.project.project.context.export,
        "get_datapoints_latest",
        mock_get_datapoints_latest,
    ), patch.object(
        controller, "_process_task"
    ):
        controller.args = argparse.Namespace(
            type=controller.TYPE_LATEST,
            with_files=False,
            dicom_to_nifti=False,
            old_format=False,
            without_masks=False,
            semantic=True,
            binary_mask=False,
            single_mask=False,
            no_consensus=False,
            png=True,
            rt_struct=True,
            clear_cache=False,
            concurrency=10,
            stage=None,  # only with "latest"
            destination=".",  # current dir
        )
        # set cache in old location to trigger a migration
        _cache_hash = controller.project.cache.set_data("datapoints", {})
        controller.project.conf.set_section(
            "datapoints",
            {"cache": _cache_hash, "timestamp": str(datetime.now().timestamp())},
        )

        # call method
        controller.handle_export()

        cache_hash = controller.project.conf.get_section("datapoints").get("cache")
        assert isinstance(cache_hash, str)

        old_cached_task_ids = controller.project.cache.get_data(
            "datapoints", cache_hash
        )
        assert old_cached_task_ids is None

        cached_task_ids = controller.project.cache.get_data("tasks", cache_hash)
        cache = controller.project.cache.get_entity(cached_task_ids[0])
        assert cached_task_ids == ["mock_task_id"]
        assert isinstance(cache, dict)
        assert cache["taskId"] == cached_task_ids[0]

        assert os.path.isdir(os.path.join(project_path, "images"))
        assert os.path.isdir(os.path.join(project_path, "segmentations"))
        assert os.path.isfile(os.path.join(project_path, "class_map.json"))
        assert os.path.isfile(os.path.join(project_path, "tasks.json"))
