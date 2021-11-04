"""Public interface to upload module."""

import asyncio
import os
from copy import deepcopy
from typing import List, Dict, Optional
import json
import uuid

import aiohttp
import rasterio
import numpy as np
from rasterio import features
import shapely
import matplotlib.pyplot as plt


from redbrick.common.context import RBContext
from redbrick.utils.async_utils import gather_with_concurrency
from redbrick.utils.logging import print_error


class Upload:
    """Primary interface to uploading new data to a project."""

    def __init__(self, context: RBContext, org_id: str, project_id: str) -> None:
        """Construct Upload object."""
        self.context = context
        self.org_id = org_id
        self.project_id = project_id

    async def _create_datapoint(
        self, session: aiohttp.ClientSession, storage_id: str, point: Dict
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
            )
        except ValueError as error:
            print_error(error)
            point_error = deepcopy(point)
            point_error["error"] = error
            return point_error
        return None

    async def _create_datapoints(
        self, storage_id: str, points: List[Dict]
    ) -> List[Dict]:
        async with aiohttp.ClientSession() as session:
            coros = [
                self._create_datapoint(session, storage_id, point) for point in points
            ]

            temp = await gather_with_concurrency(50, coros, "Creating datapoints")
            failed = []
            for val in temp:
                if val:
                    failed.append(val)
            return failed

    def create_datapoints(self, storage_id: str, points: List[Dict]) -> List[Dict]:
        """
        Create datapoints in project.

        Returns list of datapoints that failed to create.
        """
        return asyncio.run(self._create_datapoints(storage_id, points))

    def create_datapoints_from_masks(
        self, storage_id: str, mask_dir: str
    ) -> List[Dict]:
        """
        Create datapoints in a project, from a directory of masks in RBAI format.

        Returns list of datapoints that failed to create.
        """
        # Read in the class_map.json file
        if not os.path.isfile(os.path.join(mask_dir, "class_map.json")):
            raise Exception(
                "class_map.json file not found! You must provide the class_map.json file inside %s"
                % mask_dir
            )
        with open(os.path.join(mask_dir, "class_map.json"), "r") as file:
            class_map = json.load(file)

        # Create a temp categorty -> id mapping
        class_id_map = {}
        for i, category in enumerate(class_map):
            class_id_map[category] = i

        # Read in the datapoint_map.json file, if available
        if not os.path.isfile(os.path.join(mask_dir, "datapoint_map.json")):
            raise Exception(
                "datapoint_map.json file not found! You must provide"
                + " the datapoint_map.json file inside %s" % mask_dir
            )
        with open(os.path.join(mask_dir, "class_map.json"), "r") as file:
            datapoint_map = json.load(file)

        # Iterate over the PNG masks in the directory, and convert to RBAI format
        datapoints = []
        files = os.listdir(mask_dir)
        files = list(filter(lambda file: file[-3:] == "png", files))

        for file_ in files:
            mask = plt.imread(os.path.join(mask_dir, file_))
            # TODO: temporarily convert to simple binary mask
            mask = mask[:, :, 0]
            mask[np.where(mask != 0)] = 1

            polygons = Upload._mask_to_polygon(mask)
            entry: Dict = {}
            entry["labels"] = []
            label_entry: Dict = {}
            label_entry["category"] = [["object", "bus"]]  # TODO: Update
            label_entry["attributes"] = []
            label_entry["pixel"] = {}
            label_entry["pixel"]["imagesize"] = [mask.shape[1], mask.shape[0]]
            label_entry["pixel"]["regions"] = []
            label_entry["pixel"]["holes"] = []
            for polygon in polygons:
                label_entry["pixel"]["regions"] += [list(polygon.exterior.coords)]
                for interior in polygon.interiors:
                    label_entry["pixel"]["holes"] += [list(interior.coords)]

            entry["labels"] = [label_entry]  # TODO: Update
            entry["items"] = ["http://datasets.redbrickai.com/cars/07398.jpg"]
            entry["name"] = str(uuid.uuid4())
            datapoints += [entry]

        return asyncio.run(self._create_datapoints(storage_id, datapoints))

    @staticmethod
    def _mask_to_polygon(mask: np.ndarray) -> shapely.geometry.MultiPolygon:
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
