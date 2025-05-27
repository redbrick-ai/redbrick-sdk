"""Tests for `redbrick.utils.nifti`."""

import os
from typing import Dict, List, Optional
from unittest.mock import patch

import numpy as np
import nibabel as nib
import pytest


from redbrick.utils import nifti, png, rt_struct


@pytest.mark.unit
@pytest.mark.parametrize(
    ("pass_output", "expected"),
    [
        (True, np.array([[2, 2], [0, 0]])),
        (False, np.array([[2, 2], [0, 0]])),
    ],
)
def test_merge_segmentations_success(
    input_nifti_file, output_nifti_file, pass_output, expected
):
    """Test successful merge"""
    input_instance = 1
    output_instance = 2
    if pass_output is False:
        output_nifti_file = output_nifti_file.replace(".nii.gz", ".new.nii.gz")
    resp = nifti.merge_segmentations(
        input_nifti_file,
        output_nifti_file,
        {(input_instance,): output_instance},
    )
    assert resp is True
    # Load the output NIfTI file and check the data
    output_img = nib.load(output_nifti_file)
    output_data = output_img.get_fdata(caching="unchanged")
    assert np.array_equal(output_data, expected)


@pytest.mark.unit
def test_merge_segmentations_nonexistent_input_file(output_nifti_file):
    """Test when the input file does not exist"""
    input_instance = 1
    output_instance = 2
    invalid_file = "nonexistent.nii.gz"
    with pytest.raises(Exception), patch.object(nifti, "log_error") as mock_logger:
        nifti.merge_segmentations(
            invalid_file,
            output_nifti_file,
            {(input_instance,): output_instance},
        )
        exception = mock_logger.call_args[0][0]
        raise exception


@pytest.mark.unit
def test_merge_segmentations_invalid_nifti_file(input_nifti_file, output_nifti_file):
    """Test when the input file is not a valid NIfTI file"""
    from nibabel.wrapstruct import WrapStructError  # type: ignore

    input_instance = 1
    output_instance = 2
    with open(input_nifti_file, "w", encoding="utf-8") as file:
        file.write("This is not a NIfTI file.")
    with (
        pytest.raises(WrapStructError),
        patch.object(nifti, "log_error") as mock_logger,
    ):
        nifti.merge_segmentations(
            input_nifti_file,
            output_nifti_file,
            {(input_instance,): output_instance},
        )
        exception = mock_logger.call_args[0][0]
        raise exception


@pytest.mark.unit
def test_convert_to_binary_valid_input(tmpdir, mock_nifti_data, mock_labels):
    """Test successful binary conversion with valid input"""
    mock_data = mock_nifti_data
    tmpdir_path = str(tmpdir)
    nifti_file = os.path.join(tmpdir_path, "test_input.nii.gz")
    img = nib.Nifti1Image(mock_data, np.eye(4), dtype=np.uint8)
    img.to_filename(nifti_file)

    success, new_files = nifti.convert_to_binary(nifti_file, mock_labels, tmpdir_path)
    assert success
    assert len(new_files) == 2

    expected = {
        1: [[1, 1, 0], [0, 0, 1], [1, 1, 1]],
        2: [[0, 0, 1], [1, 1, 0], [0, 0, 0]],
    }
    for label in mock_labels[:2]:  # the third label won't create a new file
        instance_id = label["dicom"]["instanceid"]
        filename = os.path.join(tmpdir_path, f"instance-{instance_id}.nii.gz")

        assert os.path.isfile(filename)
        new_img = nib.Nifti1Image.from_filename(filename)
        new_data = new_img.get_fdata(caching="unchanged")
        assert new_data.shape == mock_data.shape
        assert (new_data == expected[instance_id]).all()


@pytest.mark.unit
def test_convert_to_binary_invalid_nifti_file(tmpdir, mock_labels):
    """Exception raised on conversion with non existent file"""
    nifti_file = "non_existent_file.nii.gz"
    with pytest.raises(FileNotFoundError):
        nifti.convert_to_binary(nifti_file, mock_labels, str(tmpdir))


@pytest.mark.unit
def test_convert_to_binary_no_labels(tmpdir, mock_nifti_data):
    """Ensure no files are returned on conversion with no labels"""
    mock_data = mock_nifti_data
    tmpdir_path = str(tmpdir)
    nifti_file = os.path.join(tmpdir_path, "test_input.nii.gz")

    img = nib.Nifti1Image(mock_data, np.eye(4), dtype=np.uint8)
    img.to_filename(nifti_file)

    # No labels provided
    success, new_files = nifti.convert_to_binary(nifti_file, [], tmpdir_path)
    assert success
    assert not new_files  # No new files should be created


@pytest.mark.unit
def test_convert_to_binary_no_matching_labels(tmpdir, mock_nifti_data):
    """Ensure no files are returned on conversion with no matching labels"""
    mock_data = mock_nifti_data
    tmpdir_path = str(tmpdir)
    nifti_file = os.path.join(tmpdir_path, "test_input.nii.gz")

    img = nib.Nifti1Image(mock_data, np.eye(4), dtype=np.uint8)
    img.to_filename(nifti_file)

    # Labels without matching instances
    invalid_labels = [{"dicom": {"instanceid": 99}}]
    success, new_files = nifti.convert_to_binary(
        nifti_file, invalid_labels, tmpdir_path
    )
    assert success
    assert not new_files  # No new files should be created


@pytest.mark.unit
def test_convert_to_binary_with_existing_files(tmpdir, mock_nifti_data, mock_labels):
    """Successful conversion with existing files"""
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

    success, new_files = nifti.convert_to_binary(nifti_file, mock_labels, tmpdir_path)
    assert success
    assert len(new_files) == 2

    for label in mock_labels:
        instance_id = label["dicom"]["instanceid"]
        filename = os.path.join(tmpdir_path, f"instance-{instance_id}.nii.gz")
        assert os.path.isfile(filename)


@pytest.mark.unit
def test_convert_to_binary_with_failed_saving(
    tmpdir, monkeypatch, mock_nifti_data, mock_labels
):
    """Failed conversion with non-existent file dir"""
    tmpdir_path = str(tmpdir)
    nifti_file = os.path.join(tmpdir_path, "test_input.nii.gz")

    img = nib.Nifti1Image(mock_nifti_data, np.eye(4), dtype=np.uint8)
    img.to_filename(nifti_file)

    with pytest.raises(FileNotFoundError):
        with monkeypatch.context() as ctx:
            ctx.setattr(
                os.path, "join", lambda *args: "/non_existent_directory/file.nii.gz"
            )
            _ = nifti.convert_to_binary(
                nifti_file, mock_labels, "/non_existent_directory"
            )


@pytest.mark.unit
def test_convert_to_binary_with_high_values(tmpdir, mock_labels):
    """Ensure the datatype auto-expands to np.uint16 with large data items"""
    tmpdir_path = str(tmpdir)
    nifti_file = os.path.join(tmpdir_path, "test_input.nii.gz")
    _labels = mock_labels + [{"dicom": {"instanceid": 256}}]

    mock_data = np.array([[1, 1, 2], [2, 256, 3], [3, 3, 4]])
    img = nib.Nifti1Image(mock_data, np.eye(4), dtype=np.uint16)
    img.to_filename(nifti_file)

    success, new_files = nifti.convert_to_binary(nifti_file, _labels, tmpdir_path)
    assert success
    assert len(new_files) == 3
    assert os.path.isfile(new_files[2])
    assert nib.loadsave.load(new_files[2]).dataobj.dtype == np.uint8


@pytest.mark.unit
def test_convert_to_semantic_with_binary_mask(nifti_instance_files, mock_labels):
    """Successful conversion to semantic with binary_mask=True"""
    masks = nifti_instance_files[:1]
    dirname = os.path.dirname(nifti_instance_files[0])
    binary_mask = True

    result, files = nifti.convert_to_semantic(masks, mock_labels, dirname, binary_mask)
    assert result is True
    assert len(files) == 3  # Should have 3 output files
    assert files != masks


@pytest.mark.unit
def test_convert_to_semantic_without_binary_mask(nifti_instance_files, mock_labels):
    """Successful conversion to semantic with binary_mask=False"""
    masks = nifti_instance_files[:1]
    dirname = os.path.dirname(nifti_instance_files[0])
    binary_mask = False
    result, files = nifti.convert_to_semantic(masks, mock_labels, dirname, binary_mask)
    assert result is True
    assert len(files) == 1  # Should have 1 output file
    assert files == masks  # files unchanged


@pytest.mark.unit
def test_convert_to_semantic_unsupported_taxonomy(nifti_instance_files, mock_labels):
    """Failed conversion due to unsupported taxonomy"""
    masks = nifti_instance_files[:1]
    dirname = os.path.dirname(nifti_instance_files[0])
    binary_mask = True

    result, files = nifti.convert_to_semantic(
        masks, mock_labels, dirname, binary_mask, False
    )
    assert result is False
    assert files == masks  # files remain unchanged


@pytest.mark.unit
def test_convert_to_semantic_invalid_files(nifti_instance_files, mock_labels):
    """Failed conversion due to non-existent maks file"""
    masks = ["non_existent_file.nii.gz"]
    dirname = os.path.dirname(nifti_instance_files[0])
    binary_mask = False

    with pytest.raises(FileNotFoundError):
        nifti.convert_to_semantic(masks, mock_labels, dirname, binary_mask)


@pytest.mark.unit
def test_convert_to_semantic_no_labels(nifti_instance_files):
    """Failed conversion with no labels"""
    masks = nifti_instance_files[:1]
    dirname = os.path.dirname(nifti_instance_files[0])
    labels = []
    binary_mask = True

    result, files = nifti.convert_to_semantic(masks, labels, dirname, binary_mask)
    assert result is True
    assert not files  # Should not have any output files


@pytest.mark.unit
def test_convert_to_semantic_invalid_input_masks(nifti_instance_files, mock_labels):
    """Failed conversion with invalid input masks"""
    masks = nifti_instance_files[:1]
    dirname = os.path.dirname(nifti_instance_files[0])
    for file in masks:
        with open(file, "ab") as file_:  # pylint: disable=unspecified-encoding
            file_.write(b"invalid append data")
    binary_mask = False

    result, files = nifti.convert_to_semantic(masks, mock_labels, dirname, binary_mask)
    assert result is True
    assert not files  # Should not have any output files


@pytest.mark.unit
def test_convert_nii_to_png_binary_success(nifti_instance_files_png, mock_labels):
    """Successful conversion of binary masks to PNG"""
    masks = nifti_instance_files_png
    dirname = os.path.dirname(nifti_instance_files_png[0])
    color_map = {0: (255, 255, 255), 1: (0, 0, 0)}
    binary_mask = True
    semantic_mask = False
    is_tax_v2 = True

    result, files = png.convert_nii_to_png(
        masks, color_map, mock_labels, dirname, binary_mask, semantic_mask, is_tax_v2
    )
    assert result is True
    assert len(files) == 3
    # Output PNG files should exist
    class_ids = [x["classid"] for x in mock_labels]
    assert [
        os.path.exists(os.path.join(dirname, f"mask-{catg}.png")) for catg in class_ids
    ]


@pytest.mark.unit
def test_convert_nii_to_png_binary_semantic_success(
    nifti_instance_files_png, mock_labels
):
    """Successful conversion of binary masks to PNG"""
    masks = nifti_instance_files_png
    dirname = os.path.dirname(nifti_instance_files_png[0])
    color_map = {0: (255, 255, 255), 1: (0, 0, 0)}
    binary_mask = True
    semantic_mask = True
    is_tax_v2 = True

    result, files = png.convert_nii_to_png(
        masks, color_map, mock_labels, dirname, binary_mask, semantic_mask, is_tax_v2
    )
    assert result is True
    assert len(files) == 3
    # Output PNG files should exist
    class_ids = [x["classid"] for x in mock_labels]
    assert [
        os.path.exists(os.path.join(dirname, f"mask-{catg}.png")) for catg in class_ids
    ]


@pytest.mark.unit
def test_convert_nii_to_png_non_binary_success(nifti_instance_files_png, mock_labels):
    """Successful conversion of non-binary masks to PNG"""
    masks = nifti_instance_files_png
    dirname = os.path.dirname(nifti_instance_files_png[0])
    color_map = {0: (255, 255, 255), 1: (0, 0, 0)}
    binary_mask = False
    semantic_mask = False
    is_tax_v2 = False

    result, files = png.convert_nii_to_png(
        masks, color_map, mock_labels, dirname, binary_mask, semantic_mask, is_tax_v2
    )
    assert result is True
    assert len(files) == 3
    # Output PNG files should exist
    class_ids = [x["classid"] for x in mock_labels]
    assert [
        os.path.exists(os.path.join(dirname, f"mask-{catg}.png")) for catg in class_ids
    ]


@pytest.mark.unit
def test_convert_nii_to_png_invalid_mask_file(nifti_instance_files_png, mock_labels):
    """Failed conversion due to invalid mask file"""
    masks = ["non_existent_file.nii.gz"]
    dirname = os.path.dirname(nifti_instance_files_png[0])

    color_map = {0: (255, 255, 255)}
    binary_mask = True
    semantic_mask = False
    is_tax_v2 = False

    with pytest.raises(FileNotFoundError):
        png.convert_nii_to_png(
            masks,
            color_map,
            mock_labels,
            dirname,
            binary_mask,
            semantic_mask,
            is_tax_v2,
        )


@pytest.mark.unit
def test_convert_nii_to_png_invalid_array_shape(nifti_instance_files, mock_labels):
    """Failed conversion due to non-png array shape"""
    masks = nifti_instance_files
    dirname = os.path.dirname(nifti_instance_files[0])
    color_map = {"category-0": (255, 255, 255), "category-1": (0, 0, 0)}
    binary_mask = True
    semantic_mask = True
    is_tax_v2 = True

    with pytest.raises(IndexError, match="tuple index out of range"):
        png.convert_nii_to_png(
            masks,
            color_map,
            mock_labels,
            dirname,
            binary_mask,
            semantic_mask,
            is_tax_v2,
        )


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("binary_mask", "semantic_mask", "png_mask", "expected_file_count"),
    [
        (True, True, True, 2),
        (True, True, False, 2),
        (True, False, True, 2),
        (True, False, False, 2),
        (False, True, True, 1),
        (False, True, False, 1),
        (False, False, True, 1),
        (False, False, False, 2),
    ],
)
async def test_utils_process_download(
    nifti_instance_files_png,
    mock_labels,
    binary_mask,
    semantic_mask,
    png_mask,
    expected_file_count,
):
    """Test dicom.process_download"""
    labels_path = nifti_instance_files_png[0]
    color_map = {"red": (255, 0, 0)}
    volume_index = 1

    result = await nifti.process_download(
        mock_labels[:2],
        labels_path,
        png_mask=png_mask,
        color_map=color_map,
        semantic_mask=semantic_mask,
        binary_mask=binary_mask,
        mhd_mask=False,
        volume_index=volume_index,
    )
    masks = result["masks"]

    if any([binary_mask, semantic_mask, png_mask]):
        assert len(masks) == expected_file_count
    else:
        assert masks == labels_path

    assert result["binary_mask"] == binary_mask
    assert result["semantic_mask"] == semantic_mask
    assert result["png_mask"] == png_mask

    if png_mask:
        assert all(x.endswith(".png") for x in masks)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_utils_process_upload(tmpdir, mock_labels, nifti_instance_files_png):
    """Test dicom.process_upload"""
    files = nifti_instance_files_png
    instance_ids = {1, 2, 3, 4, 5, 9}
    expected_instances = {1, 2, 5}
    instances: Dict[int, Optional[List[int]]] = {}

    for label in mock_labels:
        if label.get("dicom", {}).get("instanceid") in instance_ids:
            instances[label["dicom"]["instanceid"]] = label["dicom"].get("groupids")
            instance_ids.difference_update([label["dicom"]["instanceid"]])
            instance_ids.difference_update(label["dicom"].get("groupids") or [])

    for instance_id in instance_ids:
        instances[instance_id] = None

    png_mask = False  # not supported
    binary_mask = True
    masks = {
        _mask.split(".")[-3].split("-")[-1]: _mask for _mask in nifti_instance_files_png
    }
    label_validate = False
    prune_segmentations = False

    with patch.object(
        nifti, "config_path", return_value=str(tmpdir)
    ) as mock_config_path:
        result, segment_map, error_msg = await nifti.process_upload(
            files,
            instances,
            binary_mask,
            png_mask,
            masks,
            label_validate,
            prune_segmentations,
        )

    mock_config_path.assert_called_once()
    assert isinstance(result, str) and result.endswith("label.nii.gz")
    assert os.path.isfile(result)
    assert segment_map.keys() == expected_instances

    # Ensure no group IDs has the same value any instance ID
    assert (
        set()
        .union(*[(val or []) for val in segment_map.values()])
        .intersection(expected_instances)
        == set()
    )

    # Verify that we can produce the expected masks from the label file and group map
    expected_masks = {
        1: np.array([[[1], [1], [1]], [[1], [1], [1]], [[1], [1], [1]]]),
        2: np.array([[[0], [0], [1]], [[1], [1], [1]], [[1], [1], [1]]]),
        5: np.array([[[1], [1], [1]], [[1], [1], [1]], [[0], [0], [1]]]),
    }
    global_mask = np.asanyarray(nib.load(result).dataobj, np.uint8)
    for instance_id in expected_instances:
        selector = global_mask == instance_id
        for group_id in segment_map.get(instance_id) or []:
            selector = np.logical_or(selector, global_mask == group_id)
        mask = selector.astype(np.uint8)
        assert np.all(mask == expected_masks[instance_id]), (instance_id, mask)


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("semantic_mask", "expected_segment_map"),
    [
        (
            False,
            {
                "Segment_2": {"category": "Category2"},
                "Segment_3": {"category": "Category2"},
            },
        ),
        (True, {"Category2": {"category": "Category2"}}),
    ],
)
async def test_convert_nii_to_rt_struct(
    dicom_file_and_image, nifti_instance_files_png, semantic_mask, expected_segment_map
):
    """Test rt_struct.convert_nii_to_rt_struct"""
    from rt_utils import RTStruct  # type: ignore

    dicom_file, image_data = dicom_file_and_image
    dicom_series_path = os.path.dirname(dicom_file)
    categories = [
        {"category": "Category1", "classId": 1, "color": [255, 0, 0], "parents": []},
        {"category": "Category2", "classId": 2, "color": [180, 137, 80], "parents": []},
    ]
    segment_map = {
        "1": {"category": "Category1"},
        "2": {"category": "Category2"},
        "3": {"category": "Category2"},
    }
    result, new_segment_map = await rt_struct.convert_nii_to_rt_struct(
        nifti_instance_files_png[1:],
        dicom_series_path,
        categories,
        segment_map,
        semantic_mask,
        False,
    )
    assert result is not None
    assert isinstance(result, RTStruct)
    assert (result.series_data[0].pixel_array.astype(np.uint16) == image_data).all()
    assert new_segment_map == expected_segment_map


@pytest.mark.unit
def test_merge_rtstructs(create_rtstructs):
    """Test for `rt_struct.merge_rtstructs`"""
    rtstruct1, rtstruct2 = create_rtstructs
    # Add ROIs to the RTStructs
    mask1 = np.zeros((512, 512, 2), dtype=bool)
    mask1[2:8, 3:7, 1] = True
    rtstruct1.add_roi(mask1, name="ROI1")

    mask2 = np.zeros((512, 512, 2), dtype=bool)
    mask2[4:10, 4:8, 1] = True
    rtstruct1.add_roi(mask2, name="ROI2")

    mask2_1 = np.zeros((512, 512, 2), dtype=bool)
    mask2_1[4:9, 1:8, 1] = True
    rtstruct1.add_roi(mask2_1, name="ROI2")

    # Add ROIs to the second RTStruct
    mask3 = np.zeros((512, 512, 2), dtype=bool)
    mask3[1:7, 2:6, 1] = True
    rtstruct2.add_roi(mask3, name="ROI3")

    mask4 = np.zeros((512, 512, 2), dtype=bool)
    mask4[6:10, 5:9, 1] = True
    rtstruct2.add_roi(mask4, name="ROI4")

    # Merge the RTStructs
    merged_rtstruct = rt_struct.merge_rtstructs(rtstruct1, rtstruct2)

    # Check if the merged RTStruct contains all ROIs
    roi_names = merged_rtstruct.get_roi_names()
    assert len(roi_names) == 4
    assert "ROI1" in roi_names
    assert "ROI2" in roi_names
    assert "ROI3" in roi_names
    assert "ROI4" in roi_names
