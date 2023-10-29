"""Pytest Fixtures for tests in test.test_utils"""
import os
import shutil
import tempfile

import numpy as np
import pydicom
import pydicom._storage_sopclass_uids  # pylint: disable=protected-access
import pytest
import nibabel as nib
from rt_utils import RTStructBuilder  # type: ignore


@pytest.fixture(scope="function")
def create_temporary_files(tmpdir):
    """Fixture to create temporary files for testing"""
    tmpdir_inner = tempfile.mkdtemp(dir=tmpdir)
    file_paths = []
    for i, base in enumerate([str(tmpdir), tmpdir_inner]):
        file_path = os.path.join(base, f"labels_{i}.nii.gz")
        with open(file_path, "wb") as file:
            file.write(f"some random data: {i}".encode(encoding="utf-8"))
        file_paths.append(file_path)

    for fname in ("mask_off.png", "mask_off.txt", ".hidden.nii.gz"):
        file_path = os.path.join(str(tmpdir), fname)
        with open(file_path, "wb") as file:
            file.write(b"some random data")
        file_paths.append(file_path)

    yield str(tmpdir), file_paths
    shutil.rmtree(tmpdir_inner)


@pytest.fixture
def mock_nifti_data():
    """Get mock image data"""
    return np.array([[1, 1, 2], [2, 2, 3], [3, 3, 4]])


@pytest.fixture
def mock_nifti_data2():
    """Get mock png image data"""
    return np.random.randint(2**16, size=(512, 512, 512), dtype=np.uint16)


@pytest.fixture
def mock_labels():
    """Mock labels data for testing"""
    labels = [
        {
            "dicom": {"instanceid": 1, "groupids": [3, 4]},
            "classid": 0,
            "category": [["stub", "test1", "test7"]],
        },
        {
            "dicom": {"instanceid": 2},
            "classid": 1,
            "category": [["stub", "test2", "test8"]],
        },
        {
            "dicom": {"instanceid": 5},
            "classid": 2,
            "category": [["stub", "test2", "test9"]],
        },
    ]
    return labels


@pytest.fixture
def input_nifti_file():
    """Create a temporary NIfTI file for testing"""
    data = np.array([[1, 1], [0, 0]])
    img = nib.Nifti1Image(data, np.eye(4), dtype="compat")
    with tempfile.NamedTemporaryFile(suffix=".nii.gz", delete=False) as file:
        nib.save(img, file.name)
        yield file.name
    os.remove(file.name)


@pytest.fixture
def output_nifti_file():
    """Create a temporary NIfTI file for testing"""
    data = np.array([[2, 2], [0, 0]])
    img = nib.Nifti1Image(data, np.eye(4), dtype="compat")
    with tempfile.NamedTemporaryFile(suffix=".nii.gz", delete=False) as file:
        nib.save(img, file.name)
        yield file.name
    os.remove(file.name)


@pytest.fixture
def nifti_instance_files(tmpdir, mock_labels):  # pylint: disable=redefined-outer-name
    """Create temporary NIfTI files matching labels for testing"""
    data = [
        np.array([[1, 1, 2], [2, 2, 3], [3, 3, 4]]),
        np.array([[0, 0, 2], [2, 5, 3], [9, 3, 4]]),
        np.array([[3, 5, 2], [2, 2, 3], [0, 0, 5]]),
    ]
    dirname = str(tmpdir)
    files = []
    for idx, label in enumerate(mock_labels, start=0):
        _i_id = label["dicom"]["instanceid"]
        img = nib.Nifti1Image(data[idx], np.eye(4), dtype="compat")
        fname = os.path.join(dirname, f"instance-{_i_id}.nii.gz")
        with open(fname, "w+b") as file:
            nib.save(img, file.name)
            files.append(file.name)
    yield files
    shutil.rmtree(dirname, ignore_errors=True)


@pytest.fixture
def nifti_instance_files_png(
    tmpdir, mock_labels
):  # pylint: disable=redefined-outer-name
    """Create temporary png-style NIfTI files matching labels for testing"""
    data = [
        np.array([[[1], [1], [2]], [[2], [2], [3]], [[3], [3], [4]]]),
        np.array([[[0], [0], [2]], [[2], [5], [3]], [[9], [3], [4]]]),
        np.array([[[3], [5], [2]], [[2], [2], [3]], [[0], [0], [5]]]),
    ]
    dirname = str(tmpdir)
    files = []
    for idx, label in enumerate(mock_labels, start=0):
        _i_id = label["dicom"]["instanceid"]
        img = nib.Nifti1Image(data[idx], np.eye(4), dtype="compat")
        fname = os.path.join(dirname, f"instance-{_i_id}.nii.gz")
        with open(fname, "w+b") as file:
            nib.save(img, file.name)
            files.append(file.name)
    yield files
    shutil.rmtree(dirname, ignore_errors=True)


@pytest.fixture
def dicom_file_and_image(
    tmpdir, mock_nifti_data2
):  # pylint: disable=redefined-outer-name
    """Create temporary DICOM file for testing"""
    # pylint: disable=invalid-name
    # patch pydicom.Dataset to set missing attrs
    ds_cls = pydicom.dataset.Dataset
    ds_cls.StudyDate = None
    ds_cls.StudyTime = None
    ds_cls.StudyID = None
    ds_cls.SOPInstanceUID = None
    pydicom.dataset.Dataset = ds_cls

    # metadata
    meta = pydicom.Dataset()
    meta.MediaStorageSOPClassUID = (
        pydicom._storage_sopclass_uids.MRImageStorage  # pylint: disable=protected-access
    )
    meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
    meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian

    ds = pydicom.Dataset()
    ds.file_meta = meta
    ds.is_little_endian = True
    ds.is_implicit_VR = False
    ds.SOPClassUID = (
        pydicom._storage_sopclass_uids.MRImageStorage  # pylint: disable=protected-access
    )
    ds.PatientName = "Test^Firstname"
    ds.PatientID = "123456"
    ds.Modality = "MR"
    ds.SeriesInstanceUID = pydicom.uid.generate_uid()
    ds.StudyInstanceUID = pydicom.uid.generate_uid()
    ds.FrameOfReferenceUID = pydicom.uid.generate_uid()
    ds.BitsStored = 16
    ds.BitsAllocated = 16
    ds.SamplesPerPixel = 1
    ds.HighBit = 15
    ds.ImagesInAcquisition = "1"

    image = mock_nifti_data2
    ds.Rows = image.shape[0]
    ds.Columns = image.shape[1]
    ds.NumberOfFrames = image.shape[2]

    ds.ImagePositionPatient = r"0\0\1"
    ds.ImageOrientationPatient = r"1\0\0\0\-1\0"
    ds.ImageType = r"ORIGINAL\PRIMARY\AXIAL"
    ds.RescaleIntercept = "0"
    ds.RescaleSlope = "1"
    ds.PixelSpacing = r"1\1"
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.PixelRepresentation = 1

    pydicom.dataset.validate_file_meta(ds.file_meta, enforce_standard=True)
    ds.PixelData = image.tobytes()

    # save
    fname = os.path.join(str(tmpdir), "image.dcm")
    ds.save_as(fname, write_like_original=False)

    return fname, image


@pytest.fixture
def dicom_file_and_image_tuples(tmpdir):
    """Create a set of DICOM files for testing"""
    # pylint: disable=invalid-name
    # patch Dataset to set missing attrs
    ds_cls = pydicom.dataset.Dataset
    ds_cls.StudyDate = None
    ds_cls.StudyTime = None
    ds_cls.StudyID = None
    ds_cls.SOPInstanceUID = None
    pydicom.dataset.Dataset = ds_cls

    tuples = []
    for i in range(2):
        # metadata
        meta = pydicom.Dataset()
        meta.MediaStorageSOPClassUID = (
            pydicom._storage_sopclass_uids.MRImageStorage  # pylint: disable=protected-access
        )
        meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
        meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian

        ds = pydicom.Dataset()
        ds.file_meta = meta
        ds.is_little_endian = True
        ds.is_implicit_VR = False
        ds.SOPClassUID = (
            pydicom._storage_sopclass_uids.MRImageStorage  # pylint: disable=protected-access
        )
        ds.PatientName = "Test^Firstname"
        ds.PatientID = "123456"
        ds.Modality = "MR"
        ds.SeriesInstanceUID = pydicom.uid.generate_uid()
        ds.StudyInstanceUID = pydicom.uid.generate_uid()
        ds.FrameOfReferenceUID = pydicom.uid.generate_uid()
        ds.BitsStored = 16
        ds.BitsAllocated = 16
        ds.SamplesPerPixel = 1
        ds.HighBit = 15
        ds.ImagesInAcquisition = "1"

        image = np.random.randint(2**16, size=(512, 512, 512), dtype=np.uint16)
        ds.Rows = image.shape[0]
        ds.Columns = image.shape[1]
        ds.NumberOfFrames = image.shape[2]

        ds.ImagePositionPatient = r"0\0\1"
        ds.ImageOrientationPatient = r"1\0\0\0\-1\0"
        ds.ImageType = r"ORIGINAL\PRIMARY\AXIAL"
        ds.RescaleIntercept = "0"
        ds.RescaleSlope = "1"
        ds.PixelSpacing = r"1\1"
        ds.PhotometricInterpretation = "MONOCHROME2"
        ds.PixelRepresentation = 1

        pydicom.dataset.validate_file_meta(ds.file_meta, enforce_standard=True)
        ds.PixelData = image.tobytes()
        ds.ReferencedFrameOfReferenceSequence = [pydicom.Dataset()]

        # save
        fn = os.path.join(str(tmpdir), f"image{i}.dcm")
        ds.save_as(fn, write_like_original=False)
        tuples.append((fn, image))
    return tuples


@pytest.fixture
def create_rtstructs(
    dicom_file_and_image_tuples,
):  # pylint: disable=redefined-outer-name
    """Create RTStructs for test"""
    structs = []
    for idx, (file, _) in enumerate(dicom_file_and_image_tuples):
        dir_ = os.path.dirname(file)
        fname = os.path.join(dir_, f"test-rt-struct-{idx}.dcm")
        rtstruct = RTStructBuilder.create_new(dicom_series_path=dir_)
        rtstruct.save(fname)
        structs.append(rtstruct)
    return structs
