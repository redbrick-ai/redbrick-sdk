import os
from unittest.mock import patch

import numpy as np
import nibabel as nib
import pytest
from nibabel.filebasedimages import ImageFileError

from redbrick.utils import dicom


@pytest.mark.parametrize(
    ("equals", "pass_output", "expected"),
    [
        (True, True, np.array([[2, 2], [0, 0]])),
        (False, True, np.array([[2, 2], [2, 2]])),
        (True, False, np.array([[2, 2], [0, 0]])),
        (False, False, np.array([[0, 0], [2, 2]])),
    ]
)
def test_merge_segmentations_success(input_nifti_file, output_nifti_file, equals, pass_output, expected):
    """Test successful merge"""
    input_instance = 1
    output_instance = 2
    if pass_output is False:
        os.remove(output_nifti_file)
    resp = dicom.merge_segmentations(input_nifti_file, input_instance, equals, output_nifti_file, output_instance)
    assert resp is True
    # Load the output NIfTI file and check the data
    output_img = nib.load(output_nifti_file)
    output_data = output_img.get_fdata(caching="unchanged")
    assert np.array_equal(output_data, expected)


def test_merge_segmentations_nonexistent_input_file(output_nifti_file):
    """Test when the input file does not exist"""
    input_instance = 1
    equals = True
    output_instance = 2
    invalid_file = "nonexistent.nii.gz"
    with pytest.raises(Exception), patch.object(dicom, "log_error") as mock_logger:
        dicom.merge_segmentations(invalid_file, input_instance, equals, output_nifti_file, output_instance)
        exception = mock_logger.call_args[0][0]
        raise exception


def test_merge_segmentations_invalid_nifti_file(input_nifti_file, output_nifti_file):
    """Test when the input file is not a valid NIfTI file"""
    input_instance = 1
    equals = True
    output_instance = 2
    with open(input_nifti_file, "w") as f:
        f.write("This is not a NIfTI file.")
    with pytest.raises(ImageFileError), patch.object(dicom, "log_error") as mock_logger:
        dicom.merge_segmentations(input_nifti_file, input_instance, equals, output_nifti_file, output_instance)
        exception = mock_logger.call_args[0][0]
        raise exception


def test_convert_to_binary_valid_input(tmpdir, mock_nifti_data, mock_labels):
    mock_data = mock_nifti_data
    tmpdir_path = str(tmpdir)
    nifti_file = os.path.join(tmpdir_path, "test_input.nii.gz")
    img = nib.Nifti1Image(mock_data, np.eye(4), dtype=np.uint8)
    img.to_filename(nifti_file)

    success, new_files = dicom.convert_to_binary(nifti_file, mock_labels, tmpdir_path)
    assert success
    assert len(new_files) == 2

    expected = {
        1: [[1, 1, 0], [0, 0, 1], [1, 1, 1]],
        2: [[0, 0, 1], [1, 1, 0], [0, 0, 0]]
    }
    for label in mock_labels:
        instance_id = label["dicom"]["instanceid"]
        filename = os.path.join(tmpdir_path, f"instance-{instance_id}.nii.gz")

        assert os.path.isfile(filename)
        new_img = nib.Nifti1Image.from_filename(filename)
        new_data = new_img.get_fdata(caching="unchanged")
        assert new_data.shape == mock_data.shape
        assert (new_data == expected[instance_id]).all()


def test_convert_to_binary_invalid_nifti_file(tmpdir, mock_labels):
    nifti_file = "non_existent_file.nii.gz"
    with pytest.raises(FileNotFoundError):
        dicom.convert_to_binary(nifti_file, mock_labels, str(tmpdir))


def test_convert_to_binary_no_labels(tmpdir, mock_nifti_data):
    mock_data = mock_nifti_data
    tmpdir_path = str(tmpdir)
    nifti_file = os.path.join(tmpdir_path, "test_input.nii.gz")

    img = nib.Nifti1Image(mock_data, np.eye(4), dtype=np.uint8)
    img.to_filename(nifti_file)

    # No labels provided
    success, new_files = dicom.convert_to_binary(nifti_file, [], tmpdir_path)
    assert success
    assert not new_files  # No new files should be created


def test_convert_to_binary_no_matching_labels(tmpdir, mock_nifti_data):
    mock_data = mock_nifti_data
    tmpdir_path = str(tmpdir)
    nifti_file = os.path.join(tmpdir_path, "test_input.nii.gz")

    img = nib.Nifti1Image(mock_data, np.eye(4), dtype=np.uint8)
    img.to_filename(nifti_file)

    # Labels without matching instances
    invalid_labels = [{"dicom": {"instanceid": 99}}]
    success, new_files = dicom.convert_to_binary(nifti_file, invalid_labels, tmpdir_path)
    assert success
    assert not new_files  # No new files should be created


def test_convert_to_binary_with_existing_files(tmpdir, mock_nifti_data, mock_labels):
    mock_data = mock_nifti_data
    tmpdir_path = str(tmpdir)
    nifti_file = os.path.join(tmpdir_path, "test_input.nii.gz")

    img = nib.Nifti1Image(mock_data, np.eye(4), dtype=np.uint8)
    img.to_filename(nifti_file)

    # Create existing files
    for label in mock_labels:
        instance_id = label["dicom"]["instanceid"]
        filename = os.path.join(tmpdir_path, f"instance-{instance_id}.nii.gz")
        img.to_filename(filename)

    success, new_files = dicom.convert_to_binary(nifti_file, mock_labels, tmpdir_path)
    assert success
    assert len(new_files) == 2

    for label in mock_labels:
        instance_id = label["dicom"]["instanceid"]
        filename = os.path.join(tmpdir_path, f"instance-{instance_id}.nii.gz")
        assert os.path.isfile(filename)


def test_convert_to_binary_with_failed_saving(tmpdir, monkeypatch, mock_nifti_data, mock_labels):
    tmpdir_path = str(tmpdir)
    nifti_file = os.path.join(tmpdir_path, "test_input.nii.gz")

    img = nib.Nifti1Image(mock_nifti_data, np.eye(4), dtype=np.uint8)
    img.to_filename(nifti_file)

    with pytest.raises(Exception):
        with monkeypatch.context() as m:
            m.setattr(os.path, "join", lambda *args: "/non_existent_directory/file.nii.gz")
            _ = dicom.convert_to_binary(nifti_file, mock_labels, "/non_existent_directory")


def test_convert_to_binary_with_high_values(tmpdir, mock_labels):
    tmpdir_path = str(tmpdir)
    nifti_file = os.path.join(tmpdir_path, "test_input.nii.gz")
    _labels = mock_labels + [{"dicom": {"instanceid": 256}}]

    mock_data = np.array([[1, 1, 2], [2, 256 , 3], [3, 3, 4]])
    img = nib.Nifti1Image(mock_data, np.eye(4), dtype=np.uint8)
    img.to_filename(nifti_file)

    success, new_files = dicom.convert_to_binary(nifti_file, _labels, tmpdir_path)
    assert success
    assert len(new_files) == 3
    assert os.path.isfile(new_files[2])
    assert nib.loadsave.load(new_files[2]).dataobj.dtype == np.uint16
