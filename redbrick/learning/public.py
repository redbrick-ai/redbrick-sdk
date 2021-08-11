"""Public interface to learning module."""

import asyncio
from typing import Dict, List, Optional
from functools import partial
from copy import deepcopy
import aiohttp
import tqdm  # type: ignore

from redbrick.common.context import RBContext
from redbrick.utils.pagination import PaginationIterator
from redbrick.utils.rb_label_utils import clean_rb_label, flat_rb_format
from redbrick.utils.async_utils import gather_with_concurrency


class Learning:
    """Perform active learning and upload the results with the RedBrick API."""

    def __init__(
        self, context: RBContext, org_id: str, project_id: str, stage_name: str
    ) -> None:
        """Construct Learning module."""
        self.context = context
        self.org_id = org_id
        self.project_id = project_id
        self.stage_name = stage_name

    def get_learning_info(self) -> Dict:
        """
        Get a dictionary with lightly parsed redbrick response.

        The dictonary has fields:
            labeled
            unlabeled
            taxonomy
            cycle
        """
        cycle = self.context.learning.check_for_job(
            self.org_id, self.project_id, self.stage_name
        )
        if not cycle:
            raise Exception("No available jobs")

        my_iter = PaginationIterator(
            partial(
                self.context.learning.get_batch_of_tasks,
                self.org_id,
                self.project_id,
                self.stage_name,
                100,
            )
        )
        taxonomy, td_type = self.context.learning.get_taxonomy_and_type(
            self.org_id, self.project_id, self.stage_name
        )

        def _parse_labeled_entry(item: Dict) -> Dict:
            items_presigned = item["datapoint"]["itemsPresigned"]
            name = item["datapoint"]["name"]
            items = item["datapoint"]["items"]
            dp_id = item["datapoint"]["dpId"]
            task_id = item["taskId"]
            labels = [clean_rb_label(label) for label in item["groundTruth"]["labels"]]

            return {
                "dpId": dp_id,
                "taskId": task_id,
                "items": items,
                "itemsPresigned": items_presigned,
                "name": name,
                "labels": labels,
            }

        def _parse_unlabeled_entry(item: Dict) -> Dict:
            items_presigned = item["datapoint"]["itemsPresigned"]
            name = item["datapoint"]["name"]
            items = item["datapoint"]["items"]
            dp_id = item["datapoint"]["dpId"]
            task_id = item["taskId"]
            return {
                "taskId": task_id,
                "dpId": dp_id,
                "items": items,
                "itemsPresigned": items_presigned,
                "name": name,
            }

        labeled: List[Dict] = []
        unlabeled: List[Dict] = []

        print("Downloading tasks for active learning")
        for entry in tqdm.tqdm(my_iter, unit=" tasks"):
            # print(entry)
            if entry.get("groundTruth"):
                labeled.append(_parse_labeled_entry(entry))
            else:
                unlabeled.append(_parse_unlabeled_entry(entry))

        return {
            "labeled": labeled,
            "unlabeled": unlabeled,
            "taxonomy": taxonomy,
            "cycle": cycle,
            "type": td_type,
        }

    async def _update_task(
        self, session: aiohttp.ClientSession, cycle: int, task: Dict
    ) -> Optional[Dict]:
        """Attempt to update task."""
        try:
            await self.context.learning.send_batch_learning_results_async(
                session, self.org_id, self.project_id, self.stage_name, cycle, [task]
            )
        except Exception as error:
            print(error)
            point_error = deepcopy(task)
            point_error["error"] = error
            return point_error
        return None

    async def _update_tasks(self, cycle: int, tasks: List[Dict]) -> List[Dict]:
        async with aiohttp.ClientSession() as session:
            coros = [self._update_task(session, cycle, task) for task in tasks]
            temp = await gather_with_concurrency(
                100, coros, "Updating tasks with priorities"
            )
            failed = []
            for val in temp:
                if val:
                    failed.append(val)
            return failed

    def update_tasks(self, cycle: int, tasks: List[Dict]) -> List[Dict]:
        """
        Update tasks with new score and labels.

        Return any tasks that experienced issues.
        """
        temp = asyncio.run(self._update_tasks(cycle, tasks))

        # update cycle
        self.context.learning.set_cycle_status(
            self.org_id, self.project_id, self.stage_name, cycle, "DONE"
        )
        return temp
