"""Public interface to upload module."""

import asyncio
from copy import deepcopy
from typing import List, Dict, Optional

import aiohttp

from redbrick.common.context import RBContext
from redbrick.utils.async_utils import gather_with_concurrency


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
        except Exception as error:
            print(error)
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
