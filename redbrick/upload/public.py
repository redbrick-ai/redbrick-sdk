"""Public interface to upload module."""

import uuid
import asyncio
import os
from copy import deepcopy
from typing import List, Dict, Optional
import requests

import aiofiles
import aiohttp
import numpy as np
import shapely  # type: ignore

from redbrick.common.context import RBContext
from redbrick.utils.async_utils import gather_with_concurrency
from redbrick.utils.logging import print_error
from redbrick.common.enums import StorageMethod
from redbrick.utils.segmentation import get_file_type, check_mask_map_format


class Upload:
    """Primary interface to uploading new data to a project."""

    def __init__(
        self, context: RBContext, org_id: str, project_id: str, td_type: str
    ) -> None:
        """Construct Upload object."""
        self.context = context
        self.org_id = org_id
        self.project_id = project_id
        self.td_type = td_type

    async def _create_datapoint(
        self,
        session: aiohttp.ClientSession,
        storage_id: str,
        point: Dict,
        is_ground_truth: bool,
    ) -> Optional[Dict]:
        """Try to create a datapoint."""
        try:
            await self.context.upload.create_datapoint_async(
                session,
                self.org_id,
                self.project_id,
                storage_id,
                point["name"],
                point["items"],
                point.get("labels"),
                is_ground_truth,
            )
        except ValueError as error:
            print_error(error)
            point_error = deepcopy(point)
            point_error["error"] = error
            return point_error
        return None

    async def _create_datapoints(
        self, storage_id: str, points: List[Dict], is_ground_truth: bool
    ) -> List[Dict]:
        conn = aiohttp.TCPConnector(limit=30)
        async with aiohttp.ClientSession(connector=conn) as session:
            coros = [
                self._create_datapoint(session, storage_id, point, is_ground_truth)
                for point in points
            ]

            temp = await gather_with_concurrency(50, coros, "Creating datapoints")
            failed = []
            for val in temp:
                if val:
                    failed.append(val)

        await asyncio.sleep(0.250)  # give time to close ssl connections
        return failed

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
            dataset_name = self.project_id
            result = self.context.upload.items_upload_presign(
                self.org_id, files, dataset_name, file_type
            )
        except ValueError as error:
            print_error(error)
            raise error
        return result

    @staticmethod
    def _mask_to_polygon(
        mask: np.ndarray,
    ) -> shapely.geometry.MultiPolygon:
        """Convert masks to polygons."""
        try:
            import rasterio  # pylint: disable=import-outside-toplevel
            from rasterio import (  # pylint: disable=import-outside-toplevel
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
            all_polygons.append(shapely.geometry.shape(shape))

        polygon = shapely.geometry.MultiPolygon(all_polygons)
        if not polygon.is_valid:
            polygon = polygon.buffer(0)
            # Sometimes buffer() converts a simple Multipolygon to just a Polygon,
            # need to keep it a Multi throughout
            if polygon.type == "Polygon":
                polygon = shapely.geometry.MultiPolygon([polygon])
        return polygon

    @staticmethod
    def _upload_image_to_presigned(
        presigned_url: str, image_filepath: str, file_type: str
    ) -> None:
        """
        Upload a single image to s3 using the pre-signed url.

        Parameters
        ------------
        presigned_url: str
            The URL to upload to.

        image_filepath: str
            Local filepath of file to upload.

        file_type: str
            MIME filetype.
        """
        with open(image_filepath, "rb") as file:
            try:
                requests.put(
                    presigned_url,
                    data=file,
                    headers={"Content-Type": file_type},
                )
            except requests.exceptions.RequestException as error:
                print_error("File upload failed %s" % image_filepath)
                raise error

    @staticmethod
    async def _upload_image_to_presigned_async(
        session: aiohttp.ClientSession,
        presigned_url: str,
        image_filepath: str,
        file_type: str,
    ) -> None:
        """
        Upload a single image to s3 using the pre-signed url using asyncio.

        Parameters
        ------------
        presigned_url: str
            The URL to upload to.

        image_filepath: str
            Local filepath of file to upload.

        file_type: str
            MIME filetype.
        """
        async with aiofiles.open(image_filepath, mode="rb") as file:  # type: ignore
            contents = await file.read()
            headers = {"Content-Type": file_type}
            try:
                async with session.put(
                    presigned_url, headers=headers, data=contents
                ) as response:
                    if str(response.status) != "200":
                        raise ValueError(
                            "Error in uploading %s to RedBrick" % image_filepath
                        )
            except ValueError as error:
                raise error

    def _upload_image_items_to_s3(self, items: List[str]) -> List[Dict]:
        """
        Upload an image items list to RedBrick storage.

        Creates the presigned url using only the image name (not including
        any directory path before). This will store the image in remote
        without the directory information in the name.

        Parameters
        ------------
        items: List[str]
            [{"items": [...]}]

        Returns
        ----------
        List[Dict]
            Same return value as self._generate_upload_presigned_url
        """
        # Get the presigned url
        file_type = get_file_type(items[0])
        upload_items = [
            os.path.split(items[0])[-1]
        ]  # create presigned url, with only filename
        presigned_items = self._generate_upload_presigned_url(
            upload_items, [file_type[-1]]
        )

        # Upload the image to s3
        Upload._upload_image_to_presigned(
            presigned_items[0]["presignedUrl"], items[0], file_type[-1]
        )
        return presigned_items

    async def _upload_video_items_to_s3(self, items: List[str]) -> List[Dict]:
        """
        Upload a video items list to RedBrick Storage.

        See Also
        ---------
        ``_upload_image_items_to_s3``
        """
        # Get the presigned url
        file_types = []
        for item in items:
            file_types += [get_file_type(item)[-1]]

        upload_items = []
        for item in items:
            upload_items += [
                os.path.split(item)[-1]
            ]  # create presigned url, with only filename

        presigned_items = self._generate_upload_presigned_url(upload_items, file_types)

        conn = aiohttp.TCPConnector(limit=30)
        async with aiohttp.ClientSession(connector=conn) as session:
            coros = []
            # Upload the image frames to s3
            for i, _ in enumerate(items):
                coros.append(
                    Upload._upload_image_to_presigned_async(
                        session,
                        presigned_items[i]["presignedUrl"],
                        items[i],
                        file_types[i],
                    )
                )

            await gather_with_concurrency(20, coros, "Upload video items to RedBrick")

        await asyncio.sleep(0.250)  # give time to close ssl connections
        return presigned_items

    @staticmethod
    def mask_to_rbai(  # pylint: disable=too-many-locals
        mask: np.ndarray, class_map: Dict, items: str, name: str
    ) -> Dict:
        """Convert a mask to rbai datapoint format."""
        # Convert 3D mask into a series of 2D masks for each object
        mask_2d_stack = np.array([])
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
            List of tasks that failed upload.

        Notes
        ----------
            1. If doing direct upload, please use ``redbrick.StorageMethod.REDBRICK``
            as the storage id. Your items path must be a valid path to a locally stored image.

            2. When doing direct upload i.e. ``redbrick.StorageMethod.REDBRICK``,
            if you didn't specify a "name" field in your datapoints object,
            we will assign the "items" path to it.

        """
        # Check if user wants to do a direct upload
        if storage_id == StorageMethod.REDBRICK:
            # Direct upload for images
            if self.td_type.split("_")[0] == "IMAGE":

                for point in points:

                    # check points items
                    if len(point["items"]) != 1:
                        raise ValueError(
                            "Incorrect items format!"
                            + " Your items field must have exactly one entry."
                        )
                    if not os.path.exists(point["items"][0]):
                        raise OSError("Invalid local filepath %s" % point["items"][0])

                    # upload image items to s3
                    presigned_items = self._upload_image_items_to_s3(point["items"])

                    # update points dict with correct information
                    if "name" not in point:
                        point["name"] = point["items"][0]
                    point["items"] = [presigned_items[0]["filePath"]]

            else:
                # Direct upload for videos
                for point in points:
                    # check points
                    if len(point["items"]) < 1:
                        raise ValueError(
                            "Incorrect items format!"
                            + "Your items field for video must have atleast one entry."
                        )

                    presigned_items = asyncio.run(
                        self._upload_video_items_to_s3(point["items"])
                    )

                    # update point dicts with correct items
                    point["items"] = [
                        presigned_item["filePath"] for presigned_item in presigned_items
                    ]

        return asyncio.run(self._create_datapoints(storage_id, points, is_ground_truth))

    def create_datapoint_from_masks(
        self,
        storage_id: str,
        mask: np.ndarray,
        class_map: Dict,
        image_path: str,
    ) -> List[Dict]:
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
        List[Dict]
            List of tasks that failed upload.

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
            )

        # If storage_id is for remote storage
        items = image_path
        name = image_path

        # create datapoint
        datapoint_entry = Upload.mask_to_rbai(mask, class_map, items, name)
        return asyncio.run(
            self._create_datapoints(storage_id, [datapoint_entry], False)
        )
