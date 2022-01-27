"""Public interface to upload module."""

import uuid
import asyncio
import os
from copy import deepcopy
from typing import List, Dict, Optional
import json
import requests

import tenacity
import aiofiles
import aiohttp
import numpy as np
from shapely.geometry import MultiPolygon, shape as gen_shape

from redbrick.common.context import RBContext
from redbrick.common.enums import LabelType
from redbrick.common.constants import MAX_CONCURRENCY, MAX_RETRY_ATTEMPTS
from redbrick.common.enums import StorageMethod
from redbrick.utils.async_utils import gather_with_concurrency
from redbrick.utils.logging import print_error, handle_exception
from redbrick.utils.segmentation import check_mask_map_format
from redbrick.utils.files import VIDEO_FILE_TYPES, get_file_type


class Upload:
    """Primary interface to uploading new data to a project."""

    def __init__(
        self, context: RBContext, org_id: str, project_id: str, project_type: LabelType
    ) -> None:
        """Construct Upload object."""
        self.context = context
        self.org_id = org_id
        self.project_id = project_id
        self.project_type = project_type

    async def _create_datapoint(
        self,
        session: aiohttp.ClientSession,
        storage_id: str,
        point: Dict,
        is_ground_truth: bool,
    ) -> Dict:
        """Try to create a datapoint."""
        try:
            # Basic structural validations, rest handled by API
            assert (
                isinstance(point, dict) and point
            ), "Task object must be a non-empty dictionary"
            assert (
                "response" not in point and "error" not in point
            ), "Task object must not contain `response` or `error`"
            assert (
                "name" in point and isinstance(point["name"], str) and point["name"]
            ), "Task object must contain a valid `name`"
            assert (
                "items" in point
                and isinstance(point["items"], list)
                and (
                    len(point["items"]) == 1
                    if str(self.project_type.value).startswith("IMAGE_")
                    else point["items"]
                )
                and all(
                    map(lambda item: isinstance(item, str) and item, point["items"])
                )
            ), "`items` must be a list of urls (one for image and multiple for videoframes)"
            assert "labels" not in point or (
                isinstance(point["labels"], list)
                and all(
                    map(
                        lambda label: isinstance(label, dict) and label, point["labels"]
                    )
                )
            ), "`labels` must be a list of label objects"
            response = await self.context.upload.create_datapoint_async(
                session,
                self.org_id,
                self.project_id,
                storage_id,
                point["name"],
                point["items"],
                json.dumps(point.get("labels", [])),
                is_ground_truth,
            )
            assert response.get("taskId"), "Failed to create task"
            point_success = deepcopy(point)
            point_success["response"] = response
            return point_success
        except Exception as error:  # pylint:disable=broad-except
            print_error(error)
            point_error = deepcopy(point)
            point_error["error"] = error
            return point_error

    async def _create_datapoints(
        self, storage_id: str, points: List[Dict], is_ground_truth: bool
    ) -> List[Dict]:
        conn = aiohttp.TCPConnector(limit=MAX_CONCURRENCY)
        async with aiohttp.ClientSession(connector=conn) as session:
            coros = [
                self._create_datapoint(session, storage_id, point, is_ground_truth)
                for point in points
            ]
            tasks = await gather_with_concurrency(
                MAX_CONCURRENCY, coros, "Creating datapoints"
            )

        await asyncio.sleep(0.250)  # give time to close ssl connections
        return tasks

    async def _item_upload(
        self,
        session: aiohttp.ClientSession,
        storage_id: str,
        file_name: str,
        file_path: str,
        is_ground_truth: bool,
    ) -> Dict:
        """Try to upload an item."""
        try:
            data_type, task_type = str(self.project_type.value).split("_", 1)
            response = await self.context.upload.item_upload_async(
                session,
                self.org_id,
                self.project_id,
                storage_id,
                data_type,
                task_type,
                file_path,
                file_name,
                get_file_type(file_path)[1],
                is_ground_truth,
            )
            assert response.get("ok"), "Failed to create task"
            return {"name": file_name, "filePath": file_path, "response": response}
        except Exception as error:  # pylint:disable=broad-except
            print_error(error)
            return {"name": file_name, "filePath": file_path, "error": error}

    async def _create_task(
        self,
        session: aiohttp.ClientSession,
        storage_id: str,
        point: Dict,
        is_ground_truth: bool,
    ) -> Dict:
        if storage_id == StorageMethod.REDBRICK:
            file_types, upload_items, presigned_items = [], [], []
            try:
                for item in point["items"]:
                    file_types.append(get_file_type(item)[1])
                    upload_items.append(os.path.split(item)[-1])
                presigned_items = self._generate_upload_presigned_url(
                    upload_items, file_types
                )
            except Exception:  # pylint:disable=broad-except
                print_error(f"Failed to upload {point['name']}")
                return {
                    "name": point["name"],
                    "error": f"Failed to upload {point['name']}",
                }

            coros = [
                Upload._upload_image_to_presigned_async(
                    session,
                    presigned_items[idx]["presignedUrl"],
                    item,
                    file_types[idx],
                )
                for idx, item in enumerate(point["items"])
            ]
            # Upload the items to s3
            uploaded = await gather_with_concurrency(
                MAX_CONCURRENCY,
                coros,
                f"Uploading items for {point['name'][:57]}{point['name'][57:] and '...'}"
                if len(point["items"]) > 1
                else None,
                False,
            )

            if not all(uploaded):
                print_error(f"Failed to upload {point['name']}")
                return {
                    "name": point["name"],
                    "error": f"Failed to upload {point['name']}",
                }

            point["items"] = [
                presigned_item["filePath"] for presigned_item in presigned_items
            ]

        if (
            str(self.project_type.value).startswith("VIDEO_")
            and get_file_type(point["items"][0])[0] in VIDEO_FILE_TYPES
        ):
            return await self._item_upload(
                session,
                storage_id,
                point["name"],
                point["items"][0],
                is_ground_truth,
            )
        return await self._create_datapoint(session, storage_id, point, is_ground_truth)

    async def _create_tasks(
        self,
        storage_id: str,
        points: List[Dict],
        is_ground_truth: bool,
    ) -> List[Dict]:
        conn = aiohttp.TCPConnector(limit=MAX_CONCURRENCY)
        async with aiohttp.ClientSession(connector=conn) as session:
            coros = [
                self._create_task(session, storage_id, point, is_ground_truth)
                for point in points
            ]
            tasks = await gather_with_concurrency(
                MAX_CONCURRENCY, coros, "Creating tasks"
            )

        await asyncio.sleep(0.250)  # give time to close ssl connections
        return tasks

    def _generate_upload_presigned_url(
        self, files: List[str], file_type: List[str]
    ) -> List[Dict]:
        """
        Generate presigned url's to perform upload.

        Parameters:
        -------------
        files: List[str]
            This needs to be names of the files when it's uploaded.
            i.e. locally, the file can be image.png, but after
            uploading if you want it named image001.png, the files
            List must contain [image001.png].

        file_type: List[str]
            Corresponding file types.

        Returns
        ------------
        List[Dict]
            [
                {
                    "presignedUrl: "...", # url to upload to
                    "filePath": "..." # remote file path
                    "fileName": "..." # the same as values in files
                }
            ]
        """
        try:
            result = self.context.upload.items_upload_presign(
                self.org_id, self.project_id, files, file_type
            )
        except ValueError as error:
            print_error(error)
            raise error
        return result

    @staticmethod
    def _check_validity_of_items(items: Optional[List[str]]) -> List[str]:
        """
        Check the validity of an items entry with locally stored data.

        Returns
        ---------
        List[str]
            List of invalid items.
        """
        invalid = []
        if not (isinstance(items, list) and items):
            raise ValueError(
                "`items` must be a list of urls (one for image and multiple for videoframes)"
            )
        for item in items:
            if not (isinstance(item, str) and item and os.path.isfile(item)):
                invalid += [item]
                print_error(f"{item} is an invalid path")
                continue
            try:
                get_file_type(item)
            except ValueError as error:
                invalid += [item]
                print_error(error)

        return invalid

    @staticmethod
    def _mask_to_polygon(
        mask: np.ndarray,
    ) -> MultiPolygon:
        """Convert masks to polygons."""
        try:
            import rasterio  # pylint: disable=import-error, import-outside-toplevel
            from rasterio import (  # pylint: disable=import-error, import-outside-toplevel
                features,
            )
        except Exception as error:
            print_error(
                "For windows users, please follow the rasterio "
                + "documentation to properly install the module "
                + "https://rasterio.readthedocs.io/en/latest/installation.html "
                + "Rasterio is required by RedBrick SDK to work with masks."
            )
            raise error

        all_polygons = []
        for shape, _ in features.shapes(
            mask.astype(np.int16),
            mask=(mask > 0),
            transform=rasterio.Affine(1.0, 0, 0, 0, 1.0, 0),
        ):
            all_polygons.append(gen_shape(shape))

        polygon = MultiPolygon(all_polygons)
        if not polygon.is_valid:
            polygon = polygon.buffer(0)
            # Sometimes buffer() converts a simple Multipolygon to just a Polygon,
            # need to keep it a Multi throughout
            if polygon.type == "Polygon":
                polygon = MultiPolygon([polygon])
        return polygon

    @staticmethod
    @tenacity.retry(
        reraise=True,
        stop=tenacity.stop_after_attempt(MAX_RETRY_ATTEMPTS),
        wait=tenacity.wait_exponential(multiplier=1, min=1, max=10),
        retry=tenacity.retry_if_not_exception_type((KeyboardInterrupt,)),
        retry_error_callback=lambda _: False,
    )
    def _upload_image_to_presigned(
        presigned_url: str, file_path: str, file_type: str
    ) -> bool:
        """
        Upload a single image to s3 using the pre-signed url.

        Parameters
        ------------
        presigned_url: str
            The URL to upload to.

        file_path: str
            Local filepath of file to upload.

        file_type: str
            MIME filetype.

        Returns
        ------------
        True if successful, else False.
        """
        with open(file_path, "rb") as file_:
            try:
                requests.put(
                    presigned_url, data=file_, headers={"Content-Type": file_type}
                )
                return True
            except requests.exceptions.RequestException as err:
                raise ValueError(f"Error in uploading {file_path} to RedBrick") from err

    @staticmethod
    @tenacity.retry(
        reraise=True,
        stop=tenacity.stop_after_attempt(MAX_RETRY_ATTEMPTS),
        wait=tenacity.wait_exponential(multiplier=1, min=1, max=10),
        retry=tenacity.retry_if_not_exception_type((KeyboardInterrupt,)),
        retry_error_callback=lambda _: False,
    )
    async def _upload_image_to_presigned_async(
        session: aiohttp.ClientSession,
        presigned_url: str,
        file_path: str,
        file_type: str,
    ) -> bool:
        """
        Upload a single file to s3 using the pre-signed url using asyncio.

        Parameters
        ------------
        presigned_url: str
            The URL to upload to.

        file_path: str
            Local filepath of file to upload.

        file_type: str
            MIME filetype.

        Returns
        ------------
        True if successful, else False.
        """
        async with aiofiles.open(file_path, mode="rb") as file_:  # type: ignore
            contents = await file_.read()
            headers = {"Content-Type": file_type}

            async with session.put(
                presigned_url, headers=headers, data=contents
            ) as response:
                if response.status == 200:
                    return True
                raise ConnectionError(f"Error in uploading {file_path} to RedBrick")

    @staticmethod
    def mask_to_rbai(  # pylint: disable=too-many-locals
        mask: np.ndarray, class_map: Dict, items: str, name: str
    ) -> Dict:
        """Convert a mask to rbai datapoint format."""
        # Convert 3D mask into a series of 2D masks for each object
        mask_2d_stack: np.ndarray = np.array([])
        mask_2d_categories = []
        for _, category in enumerate(class_map):
            mask_2d = np.zeros((mask.shape[0], mask.shape[1]))
            color = class_map[category]
            class_idxs = np.where(
                (mask[:, :, 0] == color[0])
                & (mask[:, :, 1] == color[1])
                & (mask[:, :, 2] == color[2])
            )

            if len(class_idxs[0]) == 0:
                # Skip classes that aren't present
                continue

            mask_2d[class_idxs] = 1  # fill in binary mask
            mask_2d_categories += [category]

            # Stack all individual masks
            if mask_2d_stack.shape[0] == 0:
                mask_2d_stack = mask_2d
            else:
                mask_2d_stack = np.dstack((mask_2d_stack, mask_2d))  # type: ignore

        entry: Dict = {}
        entry["labels"] = []
        for depth in range(mask_2d_stack.shape[-1]):
            mask_depth = mask_2d_stack[:, :, depth]
            polygons = Upload._mask_to_polygon(mask_depth)

            label_entry: Dict = {}
            label_entry["category"] = [["object", mask_2d_categories[depth]]]
            label_entry["attributes"] = []
            label_entry["pixel"] = {}
            label_entry["pixel"]["imagesize"] = [
                mask_depth.shape[1],
                mask_depth.shape[0],
            ]
            label_entry["pixel"]["regions"] = []
            label_entry["pixel"]["holes"] = []
            for polygon in polygons:
                label_entry["pixel"]["regions"] += [list(polygon.exterior.coords)]
                for interior in polygon.interiors:
                    label_entry["pixel"]["holes"] += [list(interior.coords)]

            entry["labels"] += [label_entry]

        entry["items"] = [items]
        entry["name"] = name

        return entry

    @handle_exception
    def create_datapoints(
        self,
        storage_id: str,
        points: List[Dict],
        is_ground_truth: bool = False,
    ) -> List[Dict]:
        """
        Create datapoints in project.

        Optionally you can upload labels with your data.

        >>> project = redbrick.get_project(api_key, url, org_id, project_id)
        >>> project.upload.create_datapoints(...)

        Parameters
        --------------
        storage_id: str
            Your RedBrick AI external storage_id. This can be found under the Storage Tab
            on the RedBrick AI platform. To directly upload images to rbai,
            use redbrick.StorageMathod.REDBRICK.

        points: List[Dict]
            Please see the RedBrick AI reference documentation for overview of the format.
            https://docs.redbrickai.com/python-sdk/importing-data-and-labels

        is_ground_truth: bool = False
            If labels are provided in points above, and this parameters is set to true, the labels
            will be added to the Ground Truth stage. This is mainly useful for Active Learning.

        Returns
        -------------
        List[Dict]
            List of task objects with key `response` if successful, else `error`

        Notes
        ----------
            1. If doing direct upload, please use ``redbrick.StorageMethod.REDBRICK``
            as the storage id. Your items path must be a valid path to a locally stored image.

            2. When doing direct upload i.e. ``redbrick.StorageMethod.REDBRICK``,
            if you didn't specify a "name" field in your datapoints object,
            we will assign the "items" path to it.

        """
        created, skipped, filtered_points = [], [], []
        # Check if user wants to do a direct upload
        if storage_id == StorageMethod.REDBRICK:
            for point in points:
                # check path of items, if invalid, skip
                invalid = Upload._check_validity_of_items(point.get("items"))
                if invalid:
                    point_error = deepcopy(point)
                    point_error["error"] = "Invalid items"
                    skipped.append(point_error)
                    continue
                # update points dict with correct information
                if "name" not in point:
                    point["name"] = point["items"][0]

                filtered_points.append(deepcopy(point))
        else:
            filtered_points = list(map(deepcopy, points))  # type: ignore

        if filtered_points:
            created = asyncio.run(
                self._create_tasks(storage_id, filtered_points, is_ground_truth)
            )

        return skipped + created

    @handle_exception
    def create_datapoint_from_masks(
        self,
        storage_id: str,
        mask: np.ndarray,
        class_map: Dict,
        image_path: str,
    ) -> Dict:
        """
        Create a single datapoint with mask.

        >>> project = redbrick.get_project(api_key, url, org_id, project_id)
        >>> project.upload.create_datapoint_from_masks(...)

        Parameters
        --------------
        storage_id: str
            Your RedBrick AI external storage_id. This can be found under the Storage Tab
            on the RedBrick AI platform. Currently, this method only supports external storage
            or public storage i.e. redbrick.StorageMathod.PUBLIC (public hosted data).

        mask: np.ndarray.astype(np.uint8)
            A RGB mask with values as np.uint8. The RGB values correspond to a category,
            who's mapping can be gound in class_map.

        class_map: Dict
            Maps between the category_name in your Project Taxonomy and the RGB color of the mask.

            >>> class_map
            >>> {'category-1': [12, 22, 93], 'category-2': [1, 23, 128]...}

        image_map: str
            A valid path to the corresponding image. If storage_id is
            redbrick.StorageMethod.REDBRICK, image_map must be a
            valid path to a locally stored image.

        Returns
        -------------
        Dict
            Task object with key `response` if successful, else `error`

        Warnings
        ------------
        The category names in class_map must be valid entries in your project taxonomy. The project
        type also must be IMAGE_SEGMENTATION.

        """
        check_mask_map_format(mask, class_map)

        if storage_id == StorageMethod.REDBRICK:
            _, file_type = get_file_type(image_path)
            upload_filename = str(uuid.uuid4())

            # get pre-signed url for s3 upload
            presigned_items = self._generate_upload_presigned_url(
                [upload_filename], [file_type]
            )

            # upload to s3
            Upload._upload_image_to_presigned(
                presigned_items[0]["presignedUrl"],
                image_path,  # filename on local machine
                file_type,
            )

            # create datapoint
            items = presigned_items[0]["filePath"]
            name = image_path
            datapoint_entry = Upload.mask_to_rbai(mask, class_map, items, name)
            return asyncio.run(
                self._create_datapoints(storage_id, [datapoint_entry], False)
            )[0]

        # If storage_id is for remote storage
        items = image_path
        name = image_path

        # create datapoint
        datapoint_entry = Upload.mask_to_rbai(mask, class_map, items, name)
        return asyncio.run(
            self._create_datapoints(storage_id, [datapoint_entry], False)
        )[0]
