"""Tests for `redbrick.cli.command.upload`."""

import argparse
import json
import os.path
from typing import Dict, Optional, Tuple
from unittest.mock import AsyncMock, patch

import pytest

from redbrick import ImportTypes, StorageMethod
from redbrick.cli import public, CLIProject


@pytest.mark.unit
def test_handler(prepare_project, monkeypatch):
    """Test `CLIUploadController.handler` correctly gets project details"""
    project_path, config_path_, _, _ = prepare_project
    monkeypatch.chdir(project_path)
    _, cli = public.cli_parser(only_parser=False)

    with (
        patch("redbrick.cli.entity.creds.config_path", return_value=config_path_),
        patch.object(cli.upload, "handle_upload") as _handle_upload,
    ):
        args = argparse.Namespace(command=cli.CLONE, path=project_path)
        cli.upload.handler(args)
        _handle_upload.assert_called_once()
        assert isinstance(cli.upload.project, CLIProject)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("is_json", "use_dir", "error_msg"),
    [
        (True, False, 'Could not read json file, with "json=True"'),
        (True, True, "Could not find json file, in directory"),
        (False, True, "Could not find files in directory"),
    ],
)
def test_handle_upload(
    mock_upload_controller, monkeypatch, is_json, use_dir, error_msg
):  # pylint: disable=too-many-locals
    """Test the `CLIUploadController.handle_upload` when on different
    values of the "json" argument
    """
    controller, project_path = mock_upload_controller
    monkeypatch.chdir(project_path)

    json_filepath = os.path.join(project_path, "test.json")
    label_filepath = os.path.join(project_path, "test_task.json")
    dicom_filepath = os.path.join(project_path, "test_task.dcm")

    mock_json_data = [
        {
            "name": "",
            "segmentations": {"0": label_filepath},
            "items": [dicom_filepath],
        },
    ]
    mock_label_data = {
        "name": "",
        "segmentations": {"0": label_filepath},
        "segmentMap": {},
    }
    if is_json:
        with open(json_filepath, "w", encoding="utf-8") as file:
            json.dump(mock_json_data, file)

    with open(label_filepath, "w", encoding="utf-8") as file:
        json.dump(mock_label_data, file)

    with open(dicom_filepath, "wb") as file:
        file.write(b"stuff")

    # pylint: disable=unused-argument
    async def mock_validate_json(ctx, file_data, *args):
        return file_data

    async def mock_create_tasks(**kwargs):
        items = []
        for point in kwargs.get("points") or []:
            _items = point["items"]
            for _item in _items:
                items.append({"response": None, "name": _item})
        return items

    async def mock_gen_item_list(items_list, *args):
        return [[os.path.basename(pth) for pth in _list] for _list in items_list]

    def mock_get_taxonomy(
        org_id: str, tax_id: Optional[str], name: Optional[str]
    ) -> Dict:
        return {}

    def mock_get_label_storage(org_id: str, project_id: str) -> Tuple[str, str]:
        return (StorageMethod.REDBRICK, f"{org_id}/{project_id}")

    # pylint: enable=unused-argument

    validate_json_mock = AsyncMock(side_effect=mock_validate_json)
    create_tasks_mock = AsyncMock(side_effect=mock_create_tasks)
    gen_item_list_mock = AsyncMock(side_effect=mock_gen_item_list)

    with (
        patch("redbrick.upload.interact.validate_json", validate_json_mock),
        patch("redbrick.upload.interact.create_tasks", create_tasks_mock),
        patch.object(
            controller.project.project.upload, "generate_items_list", gen_item_list_mock
        ),
        patch.object(
            controller.project.project.context.project,
            "get_taxonomy",
            mock_get_taxonomy,
        ),
        patch.object(
            controller.project.project.context.project,
            "get_label_storage",
            mock_get_label_storage,
        ),
    ):
        _dir = project_path if use_dir else json_filepath
        controller.args = argparse.Namespace(
            directory=_dir,
            json=is_json,
            type=ImportTypes.DICOM3D,
            as_study=False,
            as_frames=True,
            segment_map=None,
            storage=controller.STORAGE_REDBRICK,
            label_storage=None,
            ground_truth=False,
            label_validate=False,
            prune_segmentations=False,
            clear_cache=False,
            concurrency=10,
            rt_struct=False,
            mhd=False,
        )
        controller.handle_upload()
        upload_cache_hash = controller.project.conf.get_option("uploads", "cache")
        upload_cache = controller.project.cache.get_data(
            "uploads", upload_cache_hash, fixed_cache=True
        )
        assert isinstance(upload_cache_hash, str), error_msg
        assert upload_cache is not None, error_msg
