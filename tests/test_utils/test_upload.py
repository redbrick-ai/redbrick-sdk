"""Tests for `redbrick.utils.upload`."""

import json
from unittest.mock import Mock, patch, AsyncMock

import pytest
from redbrick.common.enums import StorageMethod

from redbrick.utils import upload


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize("valid_state", [True, False])
async def test_validate_json(valid_state):
    """Check upload.validate_json handles valid and invalid payloads correctly"""
    input_data = [
        {"name": "item1"},
        {"name": "item2"},
        {"name": "item3"},
    ]
    storage_id = "storage_id"
    concurrency = 2

    # mock repo upload method
    mock_rb_context = AsyncMock()

    async def mock_validate_and_convert(
        arg1, input_, *args
    ):  # pylint: disable=unused-argument
        return {"isValid": valid_state, "converted": json.dumps(input_)}

    mock_rb_context.upload.validate_and_convert_to_import_format = (
        mock_validate_and_convert
    )

    # Execute the function
    result = await upload.validate_json(
        mock_rb_context, input_data, storage_id, concurrency
    )
    if valid_state is True:
        assert result == input_data
    else:
        assert result == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_process_segmentation_upload(
    nifti_instance_files_png, mock_labels, tmpdir
):
    """Test for `upload.process_segmentation_upload`"""
    files = [list(nifti_instance_files_png)[0]]
    org_id = "org_id"
    project_id = "project_id"
    task = {
        "name": "test_task",
        "labelsMap": [{"labelName": files, "seriesIndex": 0}],
        "labels": [
            label
            for label in mock_labels
            if label.get("dicom", {}).get("instanceid") in (1, 2)
        ],
        "seriesInfo": [
            {
                "binaryMask": True,
                "semanticMask": False,
                "pngMask": False,
                "masks": {"1": files[0]},
            }
        ],
    }
    project_label_storage_id = "project_label_storage_id"
    label_storage_id = "label_storage_id"
    label_validate = True
    prune_segmentations = True

    # Prepare RBContext mock
    mock_rb_context = AsyncMock()
    mock_rb_context.export.presign_items = Mock()
    mock_rb_context.export.presign_items.return_value = ["presigned_path"]
    mock_rb_context.labeling.presign_labels_path = AsyncMock()
    mock_rb_context.labeling.presign_labels_path.return_value = {
        "presignedUrl": "presigned_url",
        "filePath": "file_path",
    }

    with patch.object(upload, "download_files", return_value=["downloaded_path"]):
        with (
            patch.object(upload, "upload_files", return_value=[True]),
            patch("redbrick.utils.common_utils.config_path", return_value=str(tmpdir)),
        ):
            mock_aiohttp_session = AsyncMock()

            # Execute the function
            result = await upload.process_segmentation_upload(
                mock_rb_context,
                mock_aiohttp_session,
                org_id,
                project_id,
                task,
                label_storage_id,
                project_label_storage_id,
                label_validate,
                prune_segmentations,
            )

    assert result == [{"labelName": "file_path", "seriesIndex": 0}]
