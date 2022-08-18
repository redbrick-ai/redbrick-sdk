"""CLI upload command."""
import os
import re
import json
import asyncio
from argparse import ArgumentError, ArgumentParser, Namespace
import sys
from typing import List, Dict, Optional, Union

import tqdm  # type: ignore

from redbrick.cli.input.select import CLIInputSelect
from redbrick.cli.project import CLIProject
from redbrick.cli.cli_base import CLIUploadInterface
from redbrick.common.enums import StorageMethod, ImportTypes
from redbrick.utils.logging import print_info, print_warning
from redbrick.utils.files import (
    JSON_FILE_TYPES,
    IMAGE_FILE_TYPES,
    VIDEO_FILE_TYPES,
    ALL_FILE_TYPES,
    find_files_recursive,
)


class CLIUploadController(CLIUploadInterface):
    """CLI upload command controller."""

    def __init__(self, parser: ArgumentParser) -> None:
        """Intialize upload sub commands."""
        parser.add_argument(
            "directory",
            help="The directory containing files to upload to the project",
        )
        parser.add_argument(
            "--as-frames", action="store_true", help="Upload video from image frames"
        )
        parser.add_argument(
            "--type",
            "-t",
            nargs="?",
            default=ImportTypes.DICOM3D.value,
            help=f"Import file type {[import_type.value for import_type in ImportTypes]} "
            + f"(Default: {ImportTypes.DICOM3D.value}) *Applicable for Medical project",
        )
        parser.add_argument(
            "--as-study", action="store_true", help="Group files by study"
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Upload json files with list of task objects",
        )
        parser.add_argument(
            "--segment-map", "-m", help="Segmentation mapping file path"
        )
        parser.add_argument(
            "--storage",
            "-s",
            default=self.STORAGE_REDBRICK,
            help="Storage method: "
            + f"({self.STORAGE_REDBRICK} [default], {self.STORAGE_PUBLIC}, <storage id>)",
        )
        parser.add_argument(
            "--label-storage",
            help="Label Storage method: (same as items storage (--storage) [default],"
            + f" {self.STORAGE_REDBRICK}, {self.STORAGE_PUBLIC}, <storage id>)",
        )
        parser.add_argument(
            "--ground-truth", action="store_true", help="Upload tasks to ground truth"
        )

    def handler(self, args: Namespace) -> None:
        """Handle upload command."""
        self.args = args
        project = CLIProject.from_path()
        assert project, "Not a valid project"
        self.project = project

        self.handle_upload()

    def handle_upload(self) -> None:  # noqa: ignore=C901
        """Handle empty sub command."""
        # pylint: disable=protected-access, too-many-branches, too-many-locals, too-many-statements
        # pylint: disable=too-many-nested-blocks
        project = self.project.project

        directory = os.path.normpath(self.args.directory)
        if directory.endswith(".json") and os.path.isfile(directory):
            self.args.json = True
        elif not os.path.isdir(directory):
            raise Exception(f"{directory} is not a valid directory")

        data_type = str(project.project_type.value).split("_", 1)[0]

        if self.args.storage == self.STORAGE_REDBRICK:
            storage_id = str(StorageMethod.REDBRICK)
        elif self.args.storage == self.STORAGE_PUBLIC:
            storage_id = str(StorageMethod.PUBLIC)
        elif re.match(
            r"^[\da-f]{8}-([\da-f]{4}-){3}[\da-f]{12}$",
            self.args.storage.strip().lower(),
        ):
            storage_id = str(self.args.storage).strip().lower()
        else:
            raise ArgumentError(None, "")

        if not self.args.label_storage:
            label_storage_id = storage_id
        elif self.args.label_storage == self.STORAGE_REDBRICK:
            label_storage_id = str(StorageMethod.REDBRICK)
        elif self.args.label_storage == self.STORAGE_PUBLIC:
            label_storage_id = str(StorageMethod.PUBLIC)
        elif re.match(
            r"^[\da-f]{8}-([\da-f]{4}-){3}[\da-f]{12}$",
            self.args.label_storage.strip().lower(),
        ):
            label_storage_id = str(self.args.label_storage).strip().lower()
        else:
            raise ArgumentError(None, "")

        file_types = IMAGE_FILE_TYPES
        multiple = False
        if self.args.json:
            file_types = JSON_FILE_TYPES
        elif data_type == "VIDEO":
            if self.args.as_frames:
                multiple = True
            else:
                file_types = VIDEO_FILE_TYPES
        elif data_type == "DICOM":
            file_types = ALL_FILE_TYPES
        elif data_type != "IMAGE":
            raise Exception(
                "Project data type needs to be IMAGE, VIDEO or DICOM to upload files"
            )

        valid_file_types = ", ".join(f".{type_}[.gz]" for type_ in file_types)
        items_list: Union[List[List[str]], List[Dict]]
        if self.args.json and directory.endswith(".json") and os.path.isfile(directory):
            items_list = [[os.path.abspath(directory)]]
        else:
            print_info(f"Searching for items recursively in {directory}")
            items_list = find_files_recursive(
                directory, set(file_types.keys()), multiple
            )
            if multiple and not items_list:
                print_info(
                    "No items found. Please make sure your directories contain files of the same"
                    + f" type within them, i.e. any one of the following: ({valid_file_types})"
                )
                return

        upload_cache_hash = self.project.conf.get_option("uploads", "cache")
        upload_cache = set(
            self.project.cache.get_data("uploads", upload_cache_hash, True, True) or []
        )

        if "*" in file_types and items_list:
            import_file_type = CLIInputSelect(
                self.args.type,
                "Import file type",
                [import_type.value for import_type in ImportTypes],
            ).get()
            items_list = json.loads(
                self.project.context.upload.generate_items_list(
                    [item for items in items_list for item in items],
                    import_file_type,
                    self.args.as_study,
                    sys.platform.startswith("win"),
                )
            )

        segmentation_mapping = {}
        if self.args.segment_map:
            with open(self.args.segment_map, "r", encoding="utf-8") as file_:
                segmentation_mapping = json.load(file_)
                assert isinstance(
                    segmentation_mapping, dict
                ), "Segmentation mapping is invalid"

        points: List[Dict] = []
        uploading = set()
        if self.args.json:
            segment_map = {**segmentation_mapping}
            segmentation_mapping = {}
            print_info("Validating files")
            for item_group in tqdm.tqdm(items_list):
                with open(item_group[0], "r", encoding="utf-8") as file_:
                    file_data: List[Dict] = json.load(file_)
                if not file_data:
                    continue
                if not isinstance(file_data, list) or any(
                    not isinstance(obj, dict) for obj in file_data
                ):
                    print_warning(f"{item_group[0]} is not a list of task objects")
                    continue

                for item in file_data:
                    if (
                        item.get("items")
                        and isinstance(item.get("segmentations"), list)
                        and len(item["segmentations"]) > 1
                    ):
                        print_warning(
                            f"{item_group[0]} contains multiple segmentations."
                            + " Please use new import format: https://docs.redbrickai.com"
                            + "/python-sdk/reference/annotation-format-nifti#items-json"
                        )
                        continue

                if data_type == "DICOM":
                    if segment_map:
                        for item in file_data:
                            item["segmentMap"] = item.get("segmentMap", segment_map)

                    output = self.project.context.upload.validate_and_convert_to_import_format(
                        json.dumps(file_data), True, storage_id
                    )
                    if not output.get("isValid"):
                        print_warning(
                            f"File: {item_group[0]}\n"
                            + output.get(
                                "error",
                                "Error: Invalid format\n"
                                + "Docs: https://docs.redbrickai.com/python-sdk/reference"
                                + "/annotation-format-nifti#items-json",
                            )
                        )
                        continue

                    if output.get("converted"):
                        file_data = json.loads(output["converted"])

                if storage_id == str(StorageMethod.REDBRICK):
                    print_info(
                        f"Looking in your local file system for items mentioned in {item_group[0]}"
                    )
                for item in file_data:
                    if (
                        not isinstance(item.get("items"), list)
                        or not item["items"]
                        or not all(isinstance(i, str) for i in item["items"])
                    ):
                        print_warning(f"Invalid {item} in {item_group[0]}")
                        continue

                    if "name" not in item:
                        item["name"] = item["items"][0]
                    if item["name"] in upload_cache or item["name"] in uploading:
                        print_info(f"Skipping duplicate item name: {item['name']}")
                        continue

                    task_dir = os.path.dirname(item_group[0])
                    if "segmentations" in item:
                        if isinstance(item["segmentations"], list):
                            item["segmentations"] = {
                                str(idx): segmentation
                                for idx, segmentation in enumerate(
                                    item["segmentations"]
                                )
                            }
                        if "labelsMap" not in item and isinstance(
                            item["segmentations"], dict
                        ):
                            item["labelsMap"] = [
                                {"labelName": segmentation, "imageIndex": int(idx)}
                                if segmentation
                                else None
                                for idx, segmentation in item["segmentations"].items()
                            ]
                        del item["segmentations"]
                    elif "labelsPath" in item:
                        if "labelsMap" not in item:
                            item["labelsMap"] = [
                                {
                                    "labelName": item["labelsPath"],
                                    "imageIndex": 0,
                                }
                            ]
                        del item["labelsPath"]

                    if item.get("labelsMap"):
                        if data_type == "DICOM":
                            for label_map in item["labelsMap"]:
                                if not isinstance(label_map["labelName"], list):
                                    label_map["labelName"] = [label_map["labelName"]]
                                label_map["labelName"] = [
                                    label_name
                                    if os.path.isabs(label_name)
                                    or not os.path.exists(
                                        os.path.join(task_dir, label_name)
                                    )
                                    else os.path.abspath(
                                        os.path.join(task_dir, label_name)
                                    )
                                    for label_name in label_map["labelName"]
                                ]
                                if len(label_map["labelName"]) == 1:
                                    label_map["labelName"] = label_map["labelName"][0]
                        else:
                            del item["labelsMap"]

                    if storage_id != str(StorageMethod.REDBRICK):
                        uploading.add(item["name"])
                        points.append(item)
                        continue

                    for idx, path in enumerate(item["items"]):
                        item_path = (
                            path
                            if os.path.isabs(path)
                            else os.path.join(task_dir, path)
                        )
                        if os.path.isfile(item_path):
                            item["items"][idx] = item_path
                        else:
                            print_warning(
                                f"Could not find {path}. "
                                + "Perhaps you forgot to supply the --storage argument"
                            )
                            break
                    else:
                        uploading.add(item["name"])
                        points.append(item)
        else:
            for igroup in items_list:
                if isinstance(igroup, dict):
                    item_name = igroup.get("name")
                    item_group = list(
                        map(os.path.normpath, igroup.get("items", []) or [])
                    )
                else:
                    item_name = None
                    item_group = igroup

                if not item_group:
                    continue

                if len(item_group) > 1:
                    items_dir = os.path.dirname(item_group[0])
                    task_dir = os.path.dirname(items_dir)
                    task_name = os.path.basename(items_dir)
                else:
                    task_dir = os.path.dirname(item_group[0])
                    task_name = os.path.splitext(os.path.basename(item_group[0]))[0]

                label_data: Optional[Dict] = None

                label_file = os.path.join(task_dir, task_name + ".json")
                if os.path.isfile(label_file):
                    with open(label_file, "r", encoding="utf-8") as file_:
                        label_data = json.load(file_)

                item_name = (
                    label_data["name"]
                    if label_data and label_data.get("name")
                    else item_name
                    if item_name
                    else (
                        re.sub(
                            r"^" + re.escape(directory + os.path.sep) + r"?",
                            "",
                            (
                                os.path.dirname(item_group[0])
                                if len(item_group) > 1
                                else item_group[0]
                            ),
                        )
                        or directory
                    ).replace(os.path.sep, "/")
                )
                if item_name in upload_cache or item_name in uploading:
                    print_info(f"Skipping duplicate item name: {item_name}")
                    continue

                uploading.add(item_name)

                item = {
                    "name": item_name,
                    "items": item_group[:],
                    "labels": label_data.get("labels", []) if label_data else [],
                }
                if label_data and label_data.get("segmentMap"):
                    item["segmentMap"] = label_data["segmentMap"]
                if data_type == "DICOM":
                    if label_data and isinstance(label_data, dict):
                        if (
                            "segmentations" in label_data
                            and "labelsMap" not in label_data
                            and isinstance(label_data["segmentations"], (list, dict))
                        ):
                            if isinstance(label_data["segmentations"], list):
                                label_data["segmentations"] = {
                                    str(idx): segmentation
                                    for idx, segmentation in enumerate(
                                        label_data["segmentations"]
                                    )
                                }
                            if isinstance(label_data["segmentations"], dict):
                                label_data["labelsMap"] = [
                                    {"labelName": segmentation, "imageIndex": int(idx)}
                                    if segmentation
                                    else None
                                    for idx, segmentation in label_data[
                                        "segmentations"
                                    ].items()
                                ]
                        elif (
                            "labelsPath" in label_data and "labelsMap" not in label_data
                        ):
                            label_data["labelsMap"] = [
                                {
                                    "labelName": label_data["labelsPath"],
                                    "imageIndex": 0,
                                }
                            ]
                        if label_data.get("labelsMap"):
                            item["labelsMap"] = []
                            for label_map in label_data["labelsMap"]:
                                if not isinstance(label_map["labelName"], list):
                                    label_map["labelName"] = [label_map["labelName"]]
                                label_map["labelName"] = [
                                    label_name
                                    if os.path.isabs(label_name)
                                    or not os.path.exists(
                                        os.path.join(task_dir, label_name)
                                    )
                                    else os.path.abspath(
                                        os.path.join(task_dir, label_name)
                                    )
                                    for label_name in label_map["labelName"]
                                ]
                                if len(label_map["labelName"]) == 1:
                                    label_map["labelName"] = label_map["labelName"][0]
                                item["labelsMap"].append(
                                    {
                                        "labelName": label_map["labelName"],
                                        "imageIndex": int(label_map["imageIndex"]),
                                        "imageName": label_map.get("imageName"),
                                        "seriesId": label_map.get("seriesId"),
                                    }
                                )

                points.append(item)

        if points:
            print_info(f"Found {len(points)} items")
            loop = asyncio.get_event_loop()

            uploads = loop.run_until_complete(
                project.upload._create_tasks(
                    storage_id,
                    points,
                    segmentation_mapping,
                    self.args.ground_truth,
                    label_storage_id,
                )
            )

            for upload in uploads:
                if upload.get("response"):
                    upload_cache.add(upload["name"])

            self.project.conf.set_option(
                "uploads",
                "cache",
                self.project.cache.set_data("uploads", list(upload_cache), True),
            )
            self.project.conf.save()
        elif not items_list:
            print_info(
                "No items found. Please make sure your directories contain files of valid type,"
                + f" i.e. any one of the following: ({valid_file_types})"
            )
