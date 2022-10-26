"""Public interface to upload module."""
import shutil
import uuid
import asyncio
import os
from copy import deepcopy
from typing import List, Dict, Optional, Sequence, Set, Union
import json
from uuid import uuid4

import aiohttp
import tenacity
from tenacity.stop import stop_after_attempt
import numpy as np
from shapely.geometry import MultiPolygon, shape as gen_shape  # type: ignore
import tqdm  # type: ignore

from redbrick.common.context import RBContext
from redbrick.common.enums import LabelType
from redbrick.common.constants import MAX_CONCURRENCY
from redbrick.common.enums import StorageMethod
from redbrick.utils.async_utils import gather_with_concurrency
from redbrick.utils.logging import log_error, logger
from redbrick.utils.segmentation import check_mask_map_format
from redbrick.utils.files import (
    NIFTI_FILE_TYPES,
    download_files,
    get_file_type,
    upload_files,
)


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
        labels_map: Optional[List[Dict]] = None,
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
                labels_map,
                point.get("seriesInfo"),
                json.dumps(point["metaData"]) if point.get("metaData") else None,
                is_ground_truth,
                point.get("preAssign"),
            )
            assert response.get("taskId"), "Failed to create task"
            point_success = deepcopy(point)
            point_success["response"] = response
            return point_success
        except Exception as error:  # pylint:disable=broad-except
            if isinstance(error, AssertionError):
                log_error(error)
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

    @tenacity.retry(
        stop=stop_after_attempt(1),
        retry_error_callback=lambda _: {},
    )
    async def _create_task(
        self,
        session: aiohttp.ClientSession,
        storage_id: str,
        point: Dict,
        is_ground_truth: bool,
        label_storage_id: str,
        project_label_storage_id: str,
        label_validate: bool,
    ) -> Dict:
        # pylint: disable=too-many-locals, too-many-branches, too-many-nested-blocks
        # pylint: disable=import-outside-toplevel, too-many-statements
        from redbrick.utils.dicom import process_nifti_upload

        logger.debug(
            f"storage={storage_id}, gt={is_ground_truth}, label_storage={label_storage_id}, "
            + f"project_label_storage={project_label_storage_id}, validate={label_validate}"
        )
        if storage_id == StorageMethod.REDBRICK:
            logger.debug("Uploading files to Redbrick")
            file_types, upload_items, presigned_items = [], [], []
            try:
                for item in point["items"]:
                    file_types.append(get_file_type(item)[1])
                    upload_items.append(os.path.split(item)[-1])
                presigned_items = self._generate_upload_presigned_url(
                    upload_items, file_types
                )
                logger.debug(f"Presigned items: {presigned_items}")
            except Exception:  # pylint:disable=broad-except
                log_error(f"Failed to upload {point['name']}")
                return {
                    "name": point["name"],
                    "error": f"Failed to upload {point['name']}",
                }

            files = [
                (
                    item,
                    presigned_items[idx]["presignedUrl"],
                    file_types[idx],
                )
                for idx, item in enumerate(point["items"])
            ]
            uploaded = await upload_files(
                files,
                f"Uploading items for {point['name'][:57]}{point['name'][57:] and '...'}",
                False,
            )

            if not all(uploaded):
                log_error(f"Failed to upload {point['name']}")
                return {
                    "name": point["name"],
                    "error": f"Failed to upload {point['name']}",
                }

            point["items"] = [
                presigned_items[idx]["filePath"] for idx in range(len(point["items"]))
            ]

        labels_map: List[Dict] = []

        if (
            "labelsMap" not in point
            and point.get("segmentations")
            and len(point["segmentations"]) == len(point["items"])
        ):
            logger.debug("Converting segmentations to labelsMap")
            point["labelsMap"] = [
                {"labelName": segmentation, "imageIndex": idx}
                for idx, segmentation in enumerate(point["segmentations"])
            ]
            del point["segmentations"]
        elif "labelsMap" not in point and point.get("labelsPath"):
            logger.debug("Converting labelsPath to labelsMap")
            point["labelsMap"] = [{"labelName": point["labelsPath"], "imageIndex": 0}]
            del point["labelsPath"]

        labels_map = point.get("labelsMap", []) or []  # type: ignore
        download_dir = os.path.join(os.path.expanduser("~"), ".redbrickai", "temp")
        if not os.path.exists(download_dir):
            logger.debug(f"Creating temp directory: {download_dir}")
            os.makedirs(download_dir)
        for volume_index, label_map in enumerate(labels_map):
            logger.debug(f"Processing label map: {label_map} for volume {volume_index}")
            if not isinstance(label_map, dict) or not label_map.get("labelName"):
                logger.debug(
                    f"Skipping labelMap: {label_map} for volume {volume_index}"
                )
                continue

            input_labels_path: Optional[Union[str, List[str]]] = label_map["labelName"]
            if isinstance(input_labels_path, str) and os.path.isdir(input_labels_path):
                logger.debug("Label path is a directory")
                input_labels_path = [
                    os.path.join(input_labels_path, input_file)
                    for input_file in os.listdir(input_labels_path)
                ]
                if any(
                    not os.path.isfile(input_path) for input_path in input_labels_path
                ):
                    logger.debug("Not all paths are files")
                    input_labels_path = None
            elif input_labels_path:
                if isinstance(input_labels_path, str):
                    logger.debug("Label path is string")
                    input_labels_path = [input_labels_path]

                if not input_labels_path or any(
                    not isinstance(input_path, str) for input_path in input_labels_path
                ):
                    input_labels_path = None
                else:
                    external_paths = [
                        input_path
                        for input_path in input_labels_path
                        if not os.path.isfile(input_path)
                    ]
                    downloaded_paths: Sequence[Optional[str]] = []
                    if external_paths:
                        presigned_paths = self.context.export.presign_items(
                            self.org_id,
                            label_storage_id,
                            external_paths,
                        )

                        download_paths = [
                            os.path.join(download_dir, f"{uuid4()}.nii")
                            for _ in range(len(external_paths))
                        ]
                        downloaded_paths = await download_files(
                            list(zip(presigned_paths, download_paths)),
                            f"Downloading labels for {point.get('name') or point['items'][0]}",
                            False,
                        )
                    if any(not downloaded_path for downloaded_path in downloaded_paths):
                        input_labels_path = None
                    else:
                        input_labels_path = [
                            input_path
                            for input_path in input_labels_path
                            if input_path and os.path.isfile(input_path)
                        ] + [
                            downloaded_path
                            for downloaded_path in downloaded_paths
                            if downloaded_path
                        ]

            if input_labels_path:
                labels = point.get("labels", [])
                output_labels_path, group_map = process_nifti_upload(
                    input_labels_path,
                    set(
                        label["dicom"]["instanceid"]
                        for label in labels
                        if label.get("dicom", {}).get("instanceid")
                        and (
                            label.get("volumeindex") is None
                            or int(label.get("volumeindex")) == volume_index
                        )
                    ),
                    label_validate,
                )

                for label in labels:
                    if label.get("dicom", {}).get("instanceid") in group_map:
                        label["dicom"]["groupids"] = group_map[
                            label["dicom"]["instanceid"]
                        ]

                if (
                    output_labels_path
                    and not os.path.isfile(output_labels_path)
                    and label_storage_id != project_label_storage_id
                ):
                    presigned_path = self.context.export.presign_items(
                        self.org_id, label_storage_id, [output_labels_path]
                    )[0]
                    output_labels_path = (
                        await download_files(
                            [
                                (
                                    presigned_path,
                                    os.path.join(download_dir, f"{uuid4()}.nii"),
                                )
                            ],
                            f"Downloading labels for {point.get('name') or point['items'][0]}",
                            False,
                        )
                    )[0]

                if output_labels_path and os.path.isfile(output_labels_path):
                    file_type = NIFTI_FILE_TYPES["nii"]
                    presigned = await self.context.labeling.presign_labels_path(
                        session,
                        self.org_id,
                        self.project_id,
                        str(uuid4()),
                        file_type,
                    )
                    if (
                        await upload_files(
                            [
                                (
                                    output_labels_path,
                                    presigned["presignedUrl"],
                                    file_type,
                                )
                            ],
                            "Uploading labels for "
                            + f"{point['name'][:57]}{point['name'][57:] and '...'}",
                            False,
                        )
                    )[0]:
                        label_map["labelName"] = presigned["filePath"]
                elif output_labels_path:
                    label_map["labelName"] = output_labels_path
                else:
                    logger.debug("Empty label path")
                    return {}
            else:
                logger.debug("Invalid label files")
                return {}

        return await self._create_datapoint(
            session, storage_id, point, is_ground_truth, labels_map or None
        )

    @staticmethod
    def _map_segmentation_category(segmentation_mapping: Dict) -> List[Dict]:
        rb_segmentations = []
        for class_id, cat in segmentation_mapping.items():
            if isinstance(cat, dict):
                category = cat["category"]
                attributes = cat.get("attributes", []) or []
            else:
                category = cat
                attributes = []
            instance_id = int(class_id)
            if isinstance(category, int):
                rb_segmentations.append(
                    {
                        "categoryclass": category,
                        "attributes": attributes,
                        "dicom": {"instanceid": instance_id},
                    }
                )
            elif isinstance(category, str):
                rb_segmentations.append(
                    {
                        "categoryname": [category],
                        "attributes": attributes,
                        "dicom": {"instanceid": instance_id},
                    }
                )
            elif (
                isinstance(category, list)
                and len(category) == 1
                and isinstance(category[0], list)
                and category[0]
                and all(isinstance(item, str) for item in category[0])
            ):
                rb_segmentations.append(
                    {
                        "category": category,
                        "attributes": attributes,
                        "dicom": {"instanceid": instance_id},
                    }
                )
            elif (
                isinstance(category, list)
                and category
                and all(isinstance(item, str) for item in category)
            ):
                rb_segmentations.append(
                    {
                        "categoryname": category,
                        "attributes": attributes,
                        "dicom": {"instanceid": instance_id},
                    }
                )
            else:
                raise ValueError(f"Upload failed: Invalid category {category}")

        return rb_segmentations

    async def _create_tasks(
        self,
        storage_id: str,
        points: List[Dict],
        segmentation_mapping: Dict,
        is_ground_truth: bool,
        label_storage_id: str,
        label_validate: bool,
    ) -> List[Dict]:
        # pylint: disable=too-many-locals
        try:
            global_segmentations = Upload._map_segmentation_category(
                segmentation_mapping
            )
            for point in points:
                local_segmentations: List[Dict] = []
                if point.get("segmentMap"):
                    local_segmentations = Upload._map_segmentation_category(
                        point["segmentMap"]
                    )
                if local_segmentations or global_segmentations:
                    labels = point.get("labels", [])
                    for label in labels:
                        if label.get("dicom", {}).get("instanceid"):
                            log_error(
                                "Cannot have dicom segmentations in `labels` "
                                + f" when segmentMap is given: {point}"
                            )
                            return points
                    point["labels"] = labels + (
                        local_segmentations
                        if local_segmentations
                        else global_segmentations
                    )
        except ValueError as err:
            log_error(err)
            return points

        project_label_storage_id, _ = self.context.project.get_label_storage(
            self.org_id, self.project_id
        )

        conn = aiohttp.TCPConnector(limit=MAX_CONCURRENCY)
        async with aiohttp.ClientSession(connector=conn) as session:
            coros = [
                self._create_task(
                    session,
                    storage_id,
                    point,
                    is_ground_truth,
                    label_storage_id,
                    project_label_storage_id,
                    label_validate,
                )
                for point in points
            ]
            tasks = await gather_with_concurrency(10, coros, "Creating tasks")

        await asyncio.sleep(0.250)  # give time to close ssl connections

        temp_dir = os.path.join(os.path.expanduser("~"), ".redbrickai", "temp")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

        for point, task in zip(points, tasks):
            if not task:
                log_error(f"Error uploading {point}")

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
            log_error(error)
            raise error
        return result

    @staticmethod
    def _mask_to_polygon(
        mask: np.ndarray,
    ) -> MultiPolygon:
        """Convert masks to polygons."""
        # pylint: disable=import-error, import-outside-toplevel
        try:
            import rasterio  # type: ignore
            from rasterio import features  # type: ignore
        except Exception as error:
            log_error(
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
        return polygon  # type: ignore

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

        if len(mask_2d_stack.shape) == 2:
            mask_2d_stack = np.expand_dims(mask_2d_stack, axis=2)  # type: ignore

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
            for polygon in polygons.geoms:
                label_entry["pixel"]["regions"].append(
                    [list(map(int, coords)) for coords in polygon.exterior.coords]
                )
                for interior in polygon.interiors:
                    label_entry["pixel"]["holes"].append(
                        [list(map(int, coords)) for coords in interior.coords]
                    )

            entry["labels"] += [label_entry]

        entry["items"] = [items]
        entry["name"] = name

        return entry

    def create_datapoints(
        self,
        storage_id: str,
        points: List[Dict],
        is_ground_truth: bool = False,
        segmentation_mapping: Optional[Dict] = None,
        label_storage_id: Optional[str] = None,
        label_validate: bool = False,
    ) -> List[Dict]:
        """
        Create datapoints in project.

        Optionally you can upload labels with your data.

        >>> project = redbrick.get_project(org_id, project_id, api_key, url)
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
            will be added to the Ground Truth stage.

        segmentation_mapping: Optional[Dict] = None
            Optional mapping of semantic segmentation class ids and RedBrick categories.

        label_storage_id: Optional[str] = None
            Optional label storage id to reference nifti segmentations.
            Defaults to items storage_id if not specified.

        label_validate: bool = False
            Validate label nifti instances and segment map.

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
        if str(self.project_type.value).split("_", 1)[0] != "DICOM":
            raise Exception(
                "Uploading data to non Medical projects has been deprecated"
            )

        points = self.prepare_json_files([points], storage_id, segmentation_mapping)
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(
            self._create_tasks(
                storage_id,
                points,
                {},
                is_ground_truth,
                label_storage_id or storage_id,
                label_validate,
            )
        )

    def create_datapoint_from_masks(
        self,
        storage_id: str,
        mask: np.ndarray,
        class_map: Dict,
        image_path: str,
    ) -> Dict:
        """
        Create a single datapoint with mask.

        >>> project = redbrick.get_project(org_id, project_id, api_key, url)
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

        loop = asyncio.get_event_loop()
        if storage_id == StorageMethod.REDBRICK:
            _, file_type = get_file_type(image_path)
            upload_filename = str(uuid.uuid4())

            # get pre-signed url for s3 upload
            presigned_items = self._generate_upload_presigned_url(
                [upload_filename], [file_type]
            )

            # upload to s3
            loop.run_until_complete(
                upload_files(
                    [
                        (
                            image_path,  # filename on local machine
                            presigned_items[0]["presignedUrl"],
                            file_type,
                        )
                    ],
                    None,
                )
            )

            # create datapoint
            items = presigned_items[0]["filePath"]
            name = image_path
            datapoint_entry = Upload.mask_to_rbai(mask, class_map, items, name)
            return loop.run_until_complete(
                self._create_datapoints(storage_id, [datapoint_entry], False)
            )[0]

        # If storage_id is for remote storage
        items = image_path
        name = image_path

        # create datapoint
        datapoint_entry = Upload.mask_to_rbai(mask, class_map, items, name)
        return loop.run_until_complete(
            self._create_datapoints(storage_id, [datapoint_entry], False)
        )[0]

    def delete_tasks(self, task_ids: List[str]) -> bool:
        """Delete project tasks based on task ids.

        >>> project = redbrick.get_project(org_id, project_id, api_key, url)
        >>> project.upload.delete_tasks([...])

        Parameters
        --------------
        task_ids: List[str]
            List of task ids to delete.

        Returns
        -------------
        bool
            True if successful, else False.
        """
        return self.context.upload.delete_tasks(self.org_id, self.project_id, task_ids)

    def prepare_json_files(
        self,
        files_data: List[List[Dict]],
        storage_id: str,
        segment_map: Optional[Dict],
        task_dirs: Optional[List[str]] = None,
        uploaded: Optional[Set[str]] = None,
    ) -> List[Dict]:
        """Prepare items from json files for upload."""
        # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        points: List[Dict] = []
        uploading = set()
        logger.info("Validating files")
        if not task_dirs:
            cur_dir = os.getcwd()
            task_dirs = [cur_dir] * len(files_data)
        for file_data, task_dir in tqdm.tqdm(  # pylint: disable=too-many-nested-blocks
            zip(files_data, task_dirs)
        ):
            if not file_data:
                continue
            if not isinstance(file_data, list) or any(
                not isinstance(obj, dict) for obj in file_data
            ):
                logger.warning("Invalid items list")
                continue

            for item in file_data:
                if (
                    item.get("items")
                    and isinstance(item.get("segmentations"), list)
                    and len(item["segmentations"]) > 1
                ):
                    logger.warning(
                        "Items list contains multiple segmentations."
                        + " Please use new import format: https://docs.redbrickai.com"
                        + "/python-sdk/reference/annotation-format-nifti#items-json"
                    )
                    continue

            if segment_map:
                for item in file_data:
                    item["segmentMap"] = item.get("segmentMap", segment_map)

            output = self.context.upload.validate_and_convert_to_import_format(
                json.dumps(file_data), True, storage_id
            )
            if not output.get("isValid"):
                logger.warning(
                    output.get(
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
                logger.info("Looking in your local file system for items")
            for item in file_data:
                if (
                    not isinstance(item.get("items"), list)
                    or not item["items"]
                    or not all(isinstance(i, str) for i in item["items"])
                ):
                    logger.warning(f"Invalid {item}")
                    continue

                if "name" not in item:
                    item["name"] = item["items"][0]
                if (uploaded and item["name"] in uploaded) or item["name"] in uploading:
                    logger.info(f"Skipping duplicate item name: {item['name']}")
                    continue

                if "segmentations" in item:
                    if isinstance(item["segmentations"], list):
                        item["segmentations"] = {
                            str(idx): segmentation
                            for idx, segmentation in enumerate(item["segmentations"])
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
                    for label_map in item["labelsMap"]:
                        if not isinstance(label_map, dict):
                            label_map = {}
                        if not isinstance(label_map["labelName"], list):
                            label_map["labelName"] = [label_map["labelName"]]
                        label_map["labelName"] = [
                            label_name
                            if os.path.isabs(label_name)
                            or not os.path.exists(os.path.join(task_dir, label_name))
                            else os.path.abspath(os.path.join(task_dir, label_name))
                            for label_name in label_map["labelName"]
                        ]
                        if len(label_map["labelName"]) == 1:
                            label_map["labelName"] = label_map["labelName"][0]

                if storage_id != str(StorageMethod.REDBRICK):
                    uploading.add(item["name"])
                    points.append(item)
                    continue

                for idx, path in enumerate(item["items"]):
                    item_path = (
                        path if os.path.isabs(path) else os.path.join(task_dir, path)
                    )
                    if os.path.isfile(item_path):
                        item["items"][idx] = item_path
                    else:
                        logger.warning(
                            f"Could not find {path}. "
                            + "Perhaps you forgot to supply the --storage argument"
                        )
                        break
                else:
                    uploading.add(item["name"])
                    points.append(item)

        return points
