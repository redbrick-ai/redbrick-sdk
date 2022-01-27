"""CLI upload command."""
import os
import re
import asyncio
from argparse import ArgumentParser, Namespace

from redbrick.cli.project import CLIProject
from redbrick.cli.cli_base import CLIUploadInterface
from redbrick.common.enums import StorageMethod
from redbrick.utils.logging import print_info
from redbrick.utils.files import (
    DICOM_FILE_TYPES,
    IMAGE_FILE_TYPES,
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

    def handler(self, args: Namespace) -> None:
        """Handle upload command."""
        self.args = args
        project = CLIProject.from_path()
        assert project, "Not a valid project"
        self.project = project

        self.handle_upload()

    def handle_upload(self) -> None:
        """Handle empty sub command."""
        # pylint: disable=protected-access, too-many-branches, too-many-locals
        project = self.project.project

        directory = os.path.normpath(self.args.directory)
        if not os.path.isdir(directory):
            raise Exception(f"{directory} is not a valid directory")

        data_type = str(project.project_type.value).split("_", 1)[0]

        file_types = IMAGE_FILE_TYPES
        multiple = False
        if data_type == "VIDEO":
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
        print_info(f"Found {len(items_list)} items")

        upload_cache_hash = self.project.conf.get_option("uploads", "cache")
        upload_cache = set(
            self.project.cache.get_data("uploads", upload_cache_hash, True, True) or []
        )

        points = []
        for items in items_list:
            item_name = (
                re.sub(
                    r"^" + re.escape(directory + os.path.sep) + r"?",
                    "",
                    (os.path.dirname(items[0]) if multiple else items[0]),
                )
                or directory
            ).replace(os.path.sep, "/")
            if item_name in upload_cache:
                print_info(f"Skipping duplicate item name: {item_name}")
                continue
            points.append({"name": item_name, "items": items[:]})

        loop = asyncio.get_event_loop()
        uploads = loop.run_until_complete(
            project.upload._create_tasks(StorageMethod.REDBRICK, points, False)
        )

        for upload in uploads:
            if upload.get("response") or upload.get("error") == "Failed to create task":
                upload_cache.add(upload["name"])

        self.project.conf.set_option(
            "uploads",
            "cache",
            self.project.cache.set_data("uploads", list(upload_cache), True),
        )
        self.project.conf.save()
