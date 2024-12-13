"""Test process download."""

import os
import shutil
from typing import Callable, Dict, Generator, List, NotRequired, Optional, TypedDict
from contextlib import contextmanager
from unittest.mock import patch

import pytest
import numpy as np
from nibabel.nifti1 import Nifti1Image
from nibabel.loadsave import load as nib_load, save as nib_save

from redbrick.types.taxonomy import Taxonomy
from redbrick.utils import dicom


@contextmanager
def get_nifti_file(
    tmpdir: str, data: Optional[np.ndarray]
) -> Generator[Optional[str], None, None]:
    """Create temporary png-style NIfTI files matching labels for testing."""
    if data is None:
        yield None
        return

    with open(os.path.join(tmpdir, f"mask.nii.gz"), "w+b") as f:
        nib_save(Nifti1Image(data, np.eye(4), dtype="compat"), f.name)
        file_ = f.name

    try:
        yield file_
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


class DownloadResult(TypedDict):
    """Download result."""

    instances: Dict[Optional[int], np.ndarray]
    semantic_mask: bool
    binary_mask: bool


class DownloadParamLabelInstance(TypedDict):
    """Download param label instance."""

    instanceid: int
    groupids: NotRequired[Optional[List[int]]]


class DownloadParamLabel(TypedDict):
    """Download param label."""

    classid: int
    dicom: DownloadParamLabelInstance


class DownloadParams(TypedDict):
    """Download params."""

    data: Optional[np.ndarray]
    labels: List[DownloadParamLabel]
    expected: Callable[[bool, Optional[bool]], DownloadResult]


params: List[DownloadParams] = [
    # Empty
    {
        "data": None,
        "labels": [],
        "expected": lambda semantic_mask, binary_mask: {
            "instances": {},
            "semantic_mask": False,
            "binary_mask": False,
        },
    },
    # Plain
    {
        "data": np.array([[[3, 0]]]),
        "labels": [{"classid": 1, "dicom": {"instanceid": 3}}],
        "expected": lambda semantic_mask, binary_mask: {
            "instances": (
                {(2 if semantic_mask else 3): np.array([[[1, 0]]])}
                if binary_mask
                else {None: np.array([[[2 if semantic_mask else 3, 0]]])}
            ),
            "semantic_mask": semantic_mask,
            "binary_mask": False if binary_mask is None else binary_mask,
        },
    },
    # Group
    {
        "data": np.array([[[4, 0]]]),
        "labels": [
            {"classid": 0, "dicom": {"instanceid": 1, "groupids": [4]}},
            {"classid": 2, "dicom": {"instanceid": 2, "groupids": [4]}},
        ],
        "expected": lambda semantic_mask, binary_mask: {
            "instances": (
                {
                    (1 if semantic_mask else 1): np.array([[[1, 0]]]),
                    (3 if semantic_mask else 2): np.array([[[1, 0]]]),
                }
                if binary_mask or binary_mask is None
                else {None: np.array([[[1 if semantic_mask else 4, 0]]])}
            ),
            "semantic_mask": semantic_mask,
            "binary_mask": True if binary_mask is None else binary_mask,
        },
    },
]


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize("semantic_mask", [False, True])
@pytest.mark.parametrize("binary_mask", [None, False, True])
@pytest.mark.parametrize("params", params)
async def test_process_download(
    tmpdir: str,
    semantic_mask: bool,
    binary_mask: Optional[bool],
    params: DownloadParams,
) -> None:
    """Test dicom.process_download"""
    result = params["expected"](semantic_mask, binary_mask)
    with (
        patch.object(dicom, "config_path", return_value=tmpdir),
        get_nifti_file(tmpdir, params["data"]) as file_,
    ):
        rdata = await dicom.process_download(
            labels=params["labels"],  # type: ignore
            labels_path=file_,
            png_mask=False,
            color_map={},
            semantic_mask=semantic_mask,
            binary_mask=binary_mask,
            mhd_mask=False,
            volume_index=None,
        )

        masks = (
            []
            if rdata["masks"] is None
            else [rdata["masks"]] if isinstance(rdata["masks"], str) else rdata["masks"]
        )

        assert rdata["binary_mask"] == result["binary_mask"]
        assert rdata["semantic_mask"] == result["semantic_mask"]
        assert all(os.path.isfile(mask) for mask in masks)

        instances: List[Optional[int]] = []
        if rdata["semantic_mask"] and rdata["binary_mask"]:
            names = list(map(os.path.basename, masks))
            assert all(name.startswith("category-") for name in names), masks
            instances = [
                int(name.removeprefix("category-").removesuffix(".nii.gz"))
                for name in names
            ]

        elif rdata["binary_mask"]:
            names = list(map(os.path.basename, masks))
            assert all(name.startswith("instance-") for name in names), masks
            instances = [
                int(name.removeprefix("instance-").removesuffix(".nii.gz"))
                for name in names
            ]

        elif rdata["semantic_mask"]:
            assert os.path.basename(masks[0]) == "mask.nii.gz"
            instances = [None]

        elif result["instances"]:
            assert isinstance(rdata["masks"], str)
            assert os.path.basename(rdata["masks"]) == "mask.nii.gz"
            instances = [None]

        else:
            assert rdata["masks"] is None

        assert len(masks) == len(instances) == len(result["instances"])
        assert set(instances) == set(result["instances"].keys())

        for instance, mask in zip(instances, masks):
            arr = np.asanyarray(nib_load(mask).dataobj, np.uint16)  # type: ignore
            assert np.all(arr == result["instances"][instance]), (instance, arr, mask)
