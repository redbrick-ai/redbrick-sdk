"""Tests for `redbrick.utils.files`."""
import gzip
import os
from functools import reduce
from operator import add
from unittest.mock import patch, MagicMock

import pytest

from redbrick.utils import files


@pytest.mark.unit
def test_get_file_type():
    """Test files.get_file_type function"""
    assert files.get_file_type("image.png") == ("png", "image/png")
    assert files.get_file_type("label.nii.gz") == ("nii", "application/octet-stream")
    assert files.get_file_type("image.dcm") == ("dcm", "application/dicom")
    with pytest.raises(ValueError, match="Unsupported file type pdf!"):
        files.get_file_type("document.pdf")


@pytest.mark.unit
def test_find_files_recursive(create_temporary_files):
    """Test files.find_files_recursive function"""
    temp_dir, file_paths = create_temporary_files
    result = files.find_files_recursive(temp_dir, {"txt"})
    assert result == [[file_paths[3]]]

    # ensure it can get gzipped files
    result = files.find_files_recursive(temp_dir, {"nii"})
    assert set(reduce(add, result)) == set(file_paths[:2])

    # empty file type arg
    result = files.find_files_recursive(temp_dir, set(), multiple=True)
    assert isinstance(result, list)
    assert len(result) == 0

    # wildcard search
    result = files.find_files_recursive(temp_dir, {"*"})
    # ensure hidden files are not returned
    assert len(result) == 4
    assert set(reduce(add, result)) == set(file_paths[:4])


@pytest.mark.unit
def test_uniquify_path(create_temporary_files):
    """Test files.uniquify_path function"""
    _, file_paths = create_temporary_files
    new_path = files.uniquify_path(file_paths[0])
    assert os.path.exists(new_path) is False


@pytest.mark.unit
def test_is_dicom_file(dicom_file_and_image):
    """Test files.is_dicom_file function"""
    file_path, _ = dicom_file_and_image
    assert files.is_dicom_file(file_path) is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_upload_files(nifti_instance_files_png):
    """Test files.upload_files function"""
    # Test downloading the file
    mock_response = MagicMock()
    # Mock aiohttp client session
    with patch("aiohttp.ClientSession.put", return_value=mock_response) as mock_session:
        mock_response.__aenter__.return_value.status = 200
        mock_response.__aenter__.return_value.headers = {}
        # Test uploading the file
        file_path__url__ctype_tuples = [
            (x, "mock_url", "application/octet-stream")
            for x in nifti_instance_files_png
        ]
        result = await files.upload_files(file_path__url__ctype_tuples)

        assert result == [True, True, True]
        assert mock_session.call_count == 3

        upload_dataset = set()
        for call in mock_session.mock_calls:
            headers = {"Content-Type": "application/octet-stream"}
            assert call[1][0] == "mock_url"
            assert call[2]["headers"] == headers
            upload_dataset.add(call[2]["data"])

    file_dataset = set()
    for file_path, _, _ in file_path__url__ctype_tuples:
        with open(file_path, "rb") as file:
            file_dataset.add(file.read())

    assert upload_dataset == file_dataset


@pytest.mark.unit
@pytest.mark.asyncio
async def test_upload_files__uncompressed_file(create_temporary_files):
    """Test files.upload_files gzips uncompressed files before upload"""
    # Test downloading the file
    mock_response = MagicMock()
    # Mock aiohttp client session
    with patch("aiohttp.ClientSession.put", return_value=mock_response) as mock_session:
        mock_response.__aenter__.return_value.status = 200
        mock_response.__aenter__.return_value.headers = {}
        # Test uploading the file
        file_path__url__ctype_tuples = [
            (x, "mock_url", "application/octet-stream")
            for x in create_temporary_files[1]
        ]
        result = await files.upload_files(file_path__url__ctype_tuples)

        assert result == [True, True, True, True, True]
        assert mock_session.call_count == 5

        upload_dataset = set()
        for call in mock_session.mock_calls:
            headers = {
                "Content-Type": "application/octet-stream",
                "Content-Encoding": "gzip",
            }
            assert call[1][0] == "mock_url"
            assert call[2]["headers"] == headers
            upload_dataset.add(gzip.decompress(call[2]["data"]))

    file_dataset = set()
    for file_path, _, _ in file_path__url__ctype_tuples:
        with open(file_path, "rb") as file:
            file_dataset.add(file.read())

    assert upload_dataset == file_dataset


@pytest.mark.unit
@pytest.mark.asyncio
async def test_download_files(tmpdir):
    """Test files.download_files function"""
    # Test downloading the file
    download_path = str(tmpdir / "test")
    mock_data = b"some random data"
    mock_response = MagicMock()
    # Mock aiohttp client session
    with patch("aiohttp.ClientSession.get", return_value=mock_response):
        mock_response.__aenter__.return_value.status = 200
        mock_response.__aenter__.return_value.headers = {}
        mock_response.__aenter__.return_value.read.return_value = mock_data
        result = await files.download_files([("mock_url", download_path)], zipped=True)

    assert result == [download_path + ".gz"]
    assert os.path.isfile(result[0])
    with open(result[0], "rb") as file:
        assert gzip.decompress(file.read()) == mock_data
