"""Test process upload."""

import os
import shutil
from typing import Callable, Tuple, Dict, Generator, List, Optional, TypedDict
from contextlib import contextmanager
from unittest.mock import patch

import pytest
import numpy as np
from nibabel.nifti1 import Nifti1Image
from nibabel.loadsave import load as nib_load, save as nib_save

from redbrick.utils import dicom


@contextmanager
def get_nifti_files(
    tmpdir: str, data: Dict[Optional[int], List[np.ndarray]]
) -> Generator[Tuple[List[str], Dict[str, str]], None, None]:
    """Create temporary png-style NIfTI files matching labels for testing."""
    files: List[str] = []
    masks: Dict[str, str] = {}
    for inst, arrs in data.items():
        inst_files: List[str] = []
        for idx, arr in enumerate(arrs):
            with open(os.path.join(tmpdir, f"{inst or 0}-{idx}.nii.gz"), "w+b") as f:
                nib_save(Nifti1Image(arr, np.eye(4), dtype="compat"), f.name)
                inst_files.append(f.name)
        files.extend(inst_files)
        if inst and inst_files:
            masks[str(inst)] = inst_files[0]
    try:
        yield files, masks
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


class UploadResult(TypedDict):
    """Upload result."""

    instances: Dict[int, np.ndarray]


class UploadParams(TypedDict):
    """Upload params."""

    data: Dict[Optional[int], List[np.ndarray]]
    segment_map: Dict[int, Optional[List[int]]]
    binary_mask: bool
    expected: Callable[[bool, bool], UploadResult]


params: List[UploadParams] = [
    # Empty
    {
        "data": {},
        "segment_map": {},
        "binary_mask": False,
        "expected": lambda label_validate, prune_segmentations: {"instances": {}},
    },
    # Invalid
    {
        "data": {None: [np.array([[1]])]},
        "segment_map": {1: None},
        "binary_mask": False,
        "expected": lambda label_validate, prune_segmentations: {"instances": {}},
    },
    # Group + Invalid
    {
        "data": {None: [np.array([[[1]]]), np.array([[[[1]]]])]},
        "segment_map": {1: None},
        "binary_mask": False,
        "expected": lambda label_validate, prune_segmentations: {"instances": {}},
    },
    # Plain
    {
        "data": {None: [np.array([[[1, 20000]]])]},
        "segment_map": {1: None, 20000: None},
        "binary_mask": False,
        "expected": lambda label_validate, prune_segmentations: {
            "instances": {
                1: np.array([[[1, 0]]]),
                20000: np.array([[[0, 1]]]),
            }
        },
    },
    # Plain (extra file)
    {
        "data": {None: [np.array([[[1, 2]]], np.uint8)]},
        "segment_map": {1: None},
        "binary_mask": False,
        "expected": lambda label_validate, prune_segmentations: {
            "instances": (
                {1: np.array([[[1, 0]]])}
                if prune_segmentations
                else (
                    {}
                    if label_validate
                    else {1: np.array([[[1, 0]]]), 2: np.array([[[0, 1]]])}
                )
            )
        },
    },
    # Plain (extra map)
    {
        "data": {None: [np.array([[[1, 0]]], np.uint16)]},
        "segment_map": {1: None, 2: None},
        "binary_mask": False,
        "expected": lambda label_validate, prune_segmentations: {
            "instances": (
                {1: np.array([[[1, 0]]])}
                if prune_segmentations
                else ({} if label_validate else {1: np.array([[[1, 0]]])})
            )
        },
    },
    # Binary
    {
        "data": {1: [np.array([[[1, 2]]])]},
        "segment_map": {1: None},
        "binary_mask": True,
        "expected": lambda label_validate, prune_segmentations: {
            "instances": {1: np.array([[[1, 1]]])}
        },
    },
    # Binary (extra file)
    {
        "data": {1: [np.array([[[1, 0]]])], 2: [np.array([[[0, 1]]])]},
        "segment_map": {1: None},
        "binary_mask": True,
        "expected": lambda label_validate, prune_segmentations: {
            "instances": (
                {1: np.array([[[1, 0]]])}
                if prune_segmentations
                else (
                    {}
                    if label_validate
                    else {1: np.array([[[1, 0]]]), 2: np.array([[[0, 1]]])}
                )
            )
        },
    },
    # Binary (extra map)
    {
        "data": {1: [np.array([[[1, 0]]])]},
        "segment_map": {1: None, 2: None},
        "binary_mask": True,
        "expected": lambda label_validate, prune_segmentations: {
            "instances": (
                {1: np.array([[[1, 0]]])}
                if prune_segmentations
                else ({} if label_validate else {1: np.array([[[1, 0]]])})
            )
        },
    },
    # Multiple
    {
        "data": {
            None: [
                np.array([[[1, 2]]]),
                np.array([[[0, 3]]], np.uint16),
                np.array([[[1, 0]]], np.uint8),
            ]
        },
        "segment_map": {1: None, 2: None, 3: None},
        "binary_mask": False,
        "expected": lambda label_validate, prune_segmentations: {
            "instances": {
                1: np.array([[[1, 0]]]),
                2: np.array([[[0, 1]]]),
                3: np.array([[[0, 1]]]),
            }
        },
    },
    # Multiple (extra file)
    {
        "data": {None: [np.array([[[1, 2]]]), np.array([[[3, 4]]])]},
        "segment_map": {1: None, 2: None, 3: None},
        "binary_mask": False,
        "expected": lambda label_validate, prune_segmentations: {
            "instances": (
                {
                    1: np.array([[[1, 0]]]),
                    2: np.array([[[0, 1]]]),
                    3: np.array([[[1, 0]]]),
                }
                if prune_segmentations
                else (
                    {}
                    if label_validate
                    else {
                        1: np.array([[[1, 0]]]),
                        2: np.array([[[0, 1]]]),
                        3: np.array([[[1, 0]]]),
                        4: np.array([[[0, 1]]]),
                    }
                )
            )
        },
    },
    # Group
    {
        "data": {None: [np.array([[[1, 2, 3]]])]},
        "segment_map": {1: [3], 2: [3]},
        "binary_mask": False,
        "expected": lambda label_validate, prune_segmentations: {
            "instances": {
                1: np.array([[[1, 0, 1]]]),
                2: np.array([[[0, 1, 1]]]),
            },
        },
    },
    # Group only
    {
        "data": {None: [np.array([[[3]]])]},
        "segment_map": {1: [3], 2: [3]},
        "binary_mask": False,
        "expected": lambda label_validate, prune_segmentations: {
            "instances": {
                1: np.array([[[1]]]),
                2: np.array([[[1]]]),
            },
        },
    },
    # Multiple + Group
    {
        "data": {None: [np.array([[[1, 2, 3]]]), np.array([[[2, 2, 3]]])]},
        "segment_map": {1: [3], 2: [3]},
        "binary_mask": False,
        "expected": lambda label_validate, prune_segmentations: {
            "instances": {
                1: np.array([[[1, 0, 1]]]),
                2: np.array([[[1, 1, 1]]]),
            },
        },
    },
    # Multiple + Group (extra)
    {
        "data": {
            None: [
                np.array([[[0, 2, 0]]]),
                np.array([[[4, 2, 3]]]),
                np.array([[[0, 0, 0]]]),
                np.array([[[1, 2, 4]]]),
            ]
        },
        "segment_map": {1: [3], 2: [3]},
        "binary_mask": False,
        "expected": lambda label_validate, prune_segmentations: {
            "instances": (
                {
                    1: np.array([[[1, 0, 1]]]),
                    2: np.array([[[0, 1, 1]]]),
                }
                if prune_segmentations
                else (
                    {}
                    if label_validate
                    else {
                        1: np.array([[[1, 0, 1]]]),
                        2: np.array([[[0, 1, 1]]]),
                        4: np.array([[[1, 0, 1]]]),
                    }
                )
            )
        },
    },
    # Multiple + Non-decimal (round)
    {
        "data": {
            None: [np.array([[[0.49, 1, 0, 0]]]), np.array([[[0, 1, 1.49, 1.51]]])]
        },
        "segment_map": {1: None},
        "binary_mask": False,
        "expected": lambda label_validate, prune_segmentations: {
            "instances": (
                {1: np.array([[[0, 1, 1, 0]]])}
                if prune_segmentations
                else (
                    {}
                    if label_validate
                    else {1: np.array([[[0, 1, 1, 0]]]), 2: np.array([[[0, 0, 0, 1]]])}
                )
            )
        },
    },
]


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize("label_validate", [False, True])
@pytest.mark.parametrize("prune_segmentations", [False, True])
@pytest.mark.parametrize("params", params)
async def test_process_upload(
    tmpdir: str,
    label_validate: bool,
    prune_segmentations: bool,
    params: UploadParams,
) -> None:
    """Test dicom.process_upload"""
    result = params["expected"](label_validate, prune_segmentations)
    expected = result["instances"]
    with (
        patch.object(dicom, "config_path", return_value=tmpdir),
        get_nifti_files(tmpdir, params["data"]) as (files, masks),
    ):
        rfile, rmap, error_msg = await dicom.process_upload(
            files=files,
            instances=params["segment_map"],
            binary_mask=params["binary_mask"],
            png_mask=False,
            masks=masks,
            label_validate=label_validate,
            prune_segmentations=prune_segmentations,
        )

        assert set(rmap.keys()) == set(expected.keys())
        if not expected:
            assert not rfile
            return

        assert rfile and os.path.isfile(rfile)
        mask = np.asanyarray(nib_load(rfile).dataobj, np.uint16)  # type: ignore
        for instance, groups in rmap.items():
            assert not (set(groups or []) & set(rmap.keys()))
            arr = np.isin(mask, list({instance} | set(groups or []))).astype(np.uint8)
            assert np.all(arr == expected[instance]), (instance, arr, mask, rmap)
