import os
import shutil
import tempfile

import numpy as np
import pytest
import nibabel as nib


@pytest.fixture
def mock_nifti_data():
    return np.array([[1, 1, 2], [2, 2, 3], [3, 3, 4]])


@pytest.fixture
def mock_labels():
    # Mock labels data for testing
    mock_labels = [
        {"dicom": {"instanceid": 1, "groupids": [3, 4]}, "classid": 0, "category": [["stub", "test1", "test7"]]},
        {"dicom": {"instanceid": 2}, "classid": 1, "category": [["stub", "test2", "test8"]]},
        {"dicom": {"instanceid": 5}, "classid": 2, "category": [["stub", "test2", "test9"]]},
    ]
    return mock_labels


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


@pytest.fixture
def nifti_instance_files(tmpdir, mock_labels):
    # Create a temporary NIfTI file for testing
    data = [
        np.array([[1, 1, 2], [2, 2, 3], [3, 3, 4]]),
        np.array([[0, 0, 2], [2, 5, 3], [9, 3, 4]]),
        np.array([[3, 5, 2], [2, 2, 3], [0, 0, 5]]),
    ]
    dirname = str(tmpdir)
    files = []
    for idx, label in enumerate(mock_labels, start=0):
        _i_id = label["dicom"]["instanceid"]
        img = nib.Nifti1Image(data[idx], np.eye(4), dtype='compat')
        fname = os.path.join(dirname, f"instance-{_i_id}.nii.gz")
        with open(fname, "w+b") as f:
            nib.save(img, f.name)
            files.append(f.name)
    yield files
    shutil.rmtree(dirname, ignore_errors=True)


@pytest.fixture
def nifti_instance_files_png(tmpdir, mock_labels):
    # Create a temporary NIfTI file for testing
    data = [
        np.array([[[1], [1], [2]], [[2], [2], [3]], [[3], [3], [4]]]),
        np.array([[[0], [0], [2]], [[2], [5], [3]], [[9], [3], [4]]]),
        np.array([[[3], [5], [2]], [[2], [2], [3]], [[0], [0], [5]]]),
    ]
    dirname = str(tmpdir)
    files = []
    for idx, label in enumerate(mock_labels, start=0):
        _i_id = label["dicom"]["instanceid"]
        img = nib.Nifti1Image(data[idx], np.eye(4), dtype='compat')
        fname = os.path.join(dirname, f"instance-{_i_id}.nii.gz")
        with open(fname, "w+b") as f:
            nib.save(img, f.name)
            files.append(f.name)
    yield files
    shutil.rmtree(dirname, ignore_errors=True)
