"""CLI upload command."""
import os
import re
import json
import asyncio
from argparse import ArgumentError, ArgumentParser, Namespace
from typing import List, Dict, Optional, Union

from redbrick.cli.input.select import CLIInputSelect
from redbrick.cli.project import CLIProject
from redbrick.cli.cli_base import CLIUploadInterface
from redbrick.common.enums import StorageMethod, ImportTypes
from redbrick.utils.logging import logger
from redbrick.utils.files import find_files_recursive


class CLIUploadController(CLIUploadInterface):
    """CLI upload command controller."""

    def __init__(self, parser: ArgumentParser) -> None:
        """Intialize upload sub commands."""
        parser.add_argument(
            "directory",
            help="The directory containing files to upload to the project",
        )
        parser.add_argument(
            "--as-frames",
            action="store_true",
            help="Upload video from image frames",
        )
        parser.add_argument(
            "--type",
            "-t",
            nargs="?",
            default=ImportTypes.DICOM3D.value,
            choices=[import_type.value for import_type in ImportTypes],
            help=f"""Import file type
{['`' + import_type.value + '`' for import_type in ImportTypes]}\n
Please refer to [our documentation](https://docs.redbrickai.com/importing-data/direct-data-upload),
to understand the required folder structure and supported file types.
""",
        )
        parser.add_argument(
            "--as-study",
            action="store_true",
            help="Group files by study",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Upload json files with list of task objects",
        )
        parser.add_argument(
            "--segment-map",
            "-m",
            help="Segmentation mapping file path",
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
            help="Label Storage method: (same as items storage `--storage` [default],"
            + f" {self.STORAGE_REDBRICK}, {self.STORAGE_PUBLIC}, <storage id>)",
        )
        parser.add_argument(
            "--ground-truth",
            action="store_true",
            help="""Upload tasks directly to ground truth.""",
        )
        parser.add_argument(
            "--label-validate",
            action="store_true",
            help="""
Validate NIfTI label instances and segmentMap.
By default, the uploaded NIfTI files are not validated during upload,
which can result in invalid files being uploaded.
Using this argument validates the files before upload,
but may increase the upload time.""",
        )
        parser.add_argument(
            "--clear-cache", action="store_true", help="Clear local cache"
        )
        parser.add_argument(
            "--concurrency",
            "-c",
            type=int,
            default=10,
            help="Concurrency value (Default: 10)",
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
        logger.debug("Uploading data to project")
        project = self.project.project

        directory = os.path.normpath(self.args.directory)
        if directory.endswith(".json") and os.path.isfile(directory):
            self.args.json = True
        elif not os.path.isdir(directory):
            raise Exception(f"{directory} is not a valid directory")

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
            raise ArgumentError(None, f"Invalid upload storage: {self.args.storage}")

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
            raise ArgumentError(
                None, f"Invalid upload label storage: {self.args.label_storage}"
            )

        if self.args.clear_cache:
            self.project.cache.clear_cache(True)

        items_list: Union[List[List[str]], List[Dict]]
        if self.args.json and directory.endswith(".json") and os.path.isfile(directory):
            items_list = [[os.path.abspath(directory)]]
        else:
            logger.info(f"Searching for items recursively in {directory}")
            items_list = find_files_recursive(
                directory, set(["json" if self.args.json else "*"])
            )

        logger.debug(f"Contains {len(items_list)} items")

        upload_cache_hash = self.project.conf.get_option("uploads", "cache")
        upload_cache = set(
            self.project.cache.get_data("uploads", upload_cache_hash, True, True) or []
        )

        loop = asyncio.get_event_loop()

        if not self.args.json and items_list:
            import_file_type = CLIInputSelect(
                self.args.type,
                "Import file type",
                [import_type.value for import_type in ImportTypes],
            ).get()

            items_list = loop.run_until_complete(
                self.project.project.upload.generate_items_list(
                    items_list,
                    import_file_type,
                    self.args.as_study,
                    self.args.concurrency,
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
            files_data: List[List[Dict]] = []
            task_dirs: List[str] = []
            for item_group in items_list:
                task_dirs.append(os.path.dirname(item_group[0]))
                with open(item_group[0], "r", encoding="utf-8") as file_:
                    files_data.append(json.load(file_))
            logger.debug("Preparing json files for upload")
            points = self.project.project.upload.prepare_json_files(
                files_data,
                storage_id,
                segmentation_mapping,
                task_dirs,
                upload_cache,
                self.args.concurrency,
            )
            segmentation_mapping = {}
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
                    logger.info(f"Skipping duplicate item name: {item_name}")
                    continue

                uploading.add(item_name)

                item = {
                    "name": item_name,
                    "items": item_group[:],
                    "labels": label_data.get("labels", []) if label_data else [],
                }
                if label_data and label_data.get("segmentMap"):
                    item["segmentMap"] = label_data["segmentMap"]

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
                    elif "labelsPath" in label_data and "labelsMap" not in label_data:
                        label_data["labelsMap"] = [
                            {
                                "labelName": label_data["labelsPath"],
                                "imageIndex": 0,
                            }
                        ]
                    if label_data.get("labelsMap"):
                        item["labelsMap"] = []
                        for label_map in label_data["labelsMap"]:
                            if not isinstance(label_map, dict):
                                label_map = {}
                            if not isinstance(label_map["labelName"], list):
                                label_map["labelName"] = [label_map["labelName"]]
                            label_map["labelName"] = [
                                label_name
                                if os.path.isabs(label_name)
                                or not os.path.exists(
                                    os.path.join(task_dir, label_name)
                                )
                                else os.path.abspath(os.path.join(task_dir, label_name))
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
            logger.info(f"Found {len(points)} items")

            uploads = loop.run_until_complete(
                project.upload._create_tasks(
                    storage_id,
                    points,
                    segmentation_mapping,
                    self.args.ground_truth,
                    label_storage_id,
                    self.args.label_validate,
                    self.args.concurrency,
                    False,
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
            logger.info(
                "No items found. Please ensure that you have specified the correct data type: "
                + "DICOM3D, NIFTI3D, etc. Type `redbrick upload -h` for more options and usage"
            )
