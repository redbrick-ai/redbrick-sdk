import os
import tempfile
from unittest.mock import patch

import numpy as np
import nibabel as nib
import pytest
from nibabel.filebasedimages import ImageFileError
from nibabel.spatialimages import HeaderDataError

from redbrick.utils import dicom


@pytest.fixture
def input_nifti_file():
    # Create a temporary NIfTI file for testing
    data = np.array([[1, 1], [0, 0]])
    img = nib.Nifti1Image(data, np.eye(4), dtype='compat')
    with tempfile.NamedTemporaryFile(suffix=".nii.gz", delete=False) as f:
        nib.save(img, f.name)
        yield f.name
    os.remove(f.name)


@pytest.fixture
def output_nifti_file():
    # Create a temporary NIfTI file for testing
    data = np.array([[2, 2], [0, 0]])
    img = nib.Nifti1Image(data, np.eye(4), dtype='compat')
    with tempfile.NamedTemporaryFile(suffix=".nii.gz", delete=False) as f:
        nib.save(img, f.name)
        yield f.name
    os.remove(f.name)

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

