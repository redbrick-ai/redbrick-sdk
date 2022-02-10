"""CLI upload command."""
import os
import re
import json
import asyncio
from argparse import ArgumentError, ArgumentParser, Namespace
from typing import List, Dict, Optional

from redbrick.cli.project import CLIProject
from redbrick.cli.cli_base import CLIUploadInterface
from redbrick.common.enums import StorageMethod
from redbrick.utils.logging import print_info, print_warning
from redbrick.utils.files import (
    DICOM_FILE_TYPES,
    IMAGE_FILE_TYPES,
    JSON_FILE_TYPES,
    VIDEO_FILE_TYPES,
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
            "--json",
            action="store_true",
            help="Upload json files with list of task objects",
        )
        parser.add_argument(
            "--storage",
            "-s",
            default=self.STORAGE_REDBRICK,
            help="Storage method: "
            + f"({self.STORAGE_REDBRICK} [default], {self.STORAGE_PUBLIC}, <storage id>)",
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

    def handle_upload(self) -> None:
        """Handle empty sub command."""
        # pylint: disable=protected-access, too-many-branches, too-many-locals, too-many-statements
        project = self.project.project

        directory = os.path.normpath(self.args.directory)
        if not os.path.isdir(directory):
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
            multiple = True
            file_types = DICOM_FILE_TYPES
        elif data_type != "IMAGE":
            raise Exception(
                "Project data type needs to be IMAGE, VIDEO or DICOM to upload files"
            )

        print_info(f"Searching for items recursively in {directory}")
        items_list = find_files_recursive(directory, set(file_types.keys()), multiple)

        upload_cache_hash = self.project.conf.get_option("uploads", "cache")
        upload_cache = set(
            self.project.cache.get_data("uploads", upload_cache_hash, True, True) or []
        )

        points: List[Dict] = []
        uploading = set()
        if self.args.json:
            for item_group in items_list:
                with open(item_group[0], "r", encoding="utf-8") as file_:
                    file_data = json.load(file_)
                if not isinstance(file_data, list):
                    print_warning(f"{item_group[0]} is not a list of tasks")
                    continue
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
                    if item.get("labelsPath"):
                        label_blob_file = str(
                            item["labelsPath"]
                            if os.path.isabs(item["labelsPath"])
                            else os.path.join(task_dir, item["labelsPath"])
                        )
                        if (
                            data_type == "DICOM"
                            and label_blob_file.endswith(".nii")
                            and os.path.isfile(label_blob_file)
                        ):
                            item["labelsPath"] = label_blob_file
                        else:
                            del item["labelsPath"]

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
                            print_warning(f"{path} from {item_group[0]} does not exist")
                            break
                    else:
                        uploading.add(item["name"])
                        points.append(item)
        else:
            for item_group in items_list:
                item_name = (
                    re.sub(
                        r"^" + re.escape(directory + os.path.sep) + r"?",
                        "",
                        (os.path.dirname(item_group[0]) if multiple else item_group[0]),
                    )
                    or directory
                ).replace(os.path.sep, "/")
                if item_name in upload_cache or item_name in uploading:
                    print_info(f"Skipping duplicate item name: {item_name}")
                    continue

                uploading.add(item_name)
                if multiple:
                    items_dir = os.path.dirname(item_group[0])
                    task_dir = os.path.dirname(items_dir)
                    task_name = os.path.basename(items_dir)
                else:
                    task_dir = os.path.dirname(item_group[0])
                    task_name = os.path.splitext(os.path.basename(item_group[0]))[0]

                label_blob: Optional[str] = None
                label_data: Optional[Dict] = None

                label_file = os.path.join(task_dir, task_name + ".json")
                if os.path.isfile(label_file):
                    with open(label_file, "r", encoding="utf-8") as file_:
                        label_data = json.load(file_)

                if data_type == "DICOM":
                    if label_data and label_data.get("labelsPath"):
                        label_blob_file = (
                            label_data["labelsPath"]
                            if os.path.isabs(label_data["labelsPath"])
                            else os.path.join(task_dir, label_data["labelsPath"])
                        )
                        if os.path.isfile(label_blob_file):
                            label_blob = label_blob_file
                    elif os.path.isfile(os.path.join(task_dir, task_name + ".nii")):
                        label_blob = os.path.join(task_dir, task_name + ".nii")

                item = {"name": item_name, "items": item_group[:]}
                if (
                    label_data
                    and isinstance(label_data.get("labels"), list)
                    and (data_type != "DICOM" or label_blob)
                ):
                    item["labels"] = label_data["labels"]
                    if label_blob:
                        item["labelsPath"] = label_blob
                points.append(item)

        print_info(f"Found {len(points)} items")

        loop = asyncio.get_event_loop()
        uploads = loop.run_until_complete(
            project.upload._create_tasks(storage_id, points, self.args.ground_truth)
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
