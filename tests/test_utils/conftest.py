import os
import tempfile

import numpy as np
import pytest
import nibabel as nib


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
def mock_nifti_data():
    return np.array([[1, 1, 2], [2, 2, 3], [3, 3, 4]])


@pytest.fixture
def mock_affine_and_header():
    return np.eye(4), None