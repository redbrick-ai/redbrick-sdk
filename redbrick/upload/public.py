"""Public interface to upload module."""

import uuid
import asyncio
from copy import deepcopy
from typing import List, Dict, Optional
import requests

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

    def __init__(self, context: RBContext, org_id: str, project_id: str) -> None:
        """Construct Upload object."""
        self.context = context
        self.org_id = org_id
        self.project_id = project_id

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
            on the RedBrick AI platform. Currently, this method only supports external storage
            or public storage i.e. redbrick.StorageMathod.PUBLIC (public hosted data).

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
        """
        return asyncio.run(self._create_datapoints(storage_id, points, is_ground_truth))

    def _items_list_upload_presign(
        self, files: List[str], file_type: List[str]
    ) -> List[Dict]:
        """Generate presigned url's to perform upload."""
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
    def upload_image_to_presigned(
        presigned_url: str, image_filepath: str, file_type: str
    ) -> None:
        """Upload a single image to s3 using the pre-signed url."""
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
            presigned_items = self._items_list_upload_presign(
                [upload_filename], [file_type]
            )

            # upload to s3
            Upload.upload_image_to_presigned(
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
