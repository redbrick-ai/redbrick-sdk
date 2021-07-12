"""Public interface to labeling module."""

import asyncio
from typing import List, Dict, Optional
from copy import deepcopy
import aiohttp

from redbrick.common.context import RBContext
from redbrick.utils.async_utils import gather_with_concurrency
from redbrick.utils.rb_label_utils import clean_rb_label


class Labeling:
    """Perform automated labeling tasks."""

    def __init__(
        self, context: RBContext, org_id: str, project_id: str, review: bool = False
    ) -> None:
        """Construct Labeling."""
        self.context = context
        self.org_id = org_id
        self.project_id = project_id
        self.review = review

    def get_tasks(self, stage_name: str, count: int = 1) -> List[Dict]:
        """Get a list of tasks."""
        tasks = self.context.labeling.get_labeling_tasks(
            self.org_id, self.project_id, stage_name, count=count
        )

        def _clean_tasks(task: Dict) -> Dict:
            task_id = task["taskId"]
            labels = task.get("taskData", {}).get("labels", [])
            labels_cleaned = [clean_rb_label(label) for label in labels]

            items = task["datapoint"]["items"]
            items_presigned = task["datapoint"]["itemsPresigned"]
            name = task["datapoint"]["name"]

            return {
                "taskId": task_id,
                "labels": labels,
                "items": items,
                "itemsPresigned": items_presigned,
                "name": name,
            }

        return [_clean_tasks(task) for task in tasks]

    async def _put_task(
        self, session: aiohttp.ClientSession, stage_name: str, task: Dict
    ) -> Optional[Dict]:
        task_id = task["taskId"]
        try:
            if self.review:
                review_val = task["reviewVal"]
                await self.context.labeling.put_review_task_result(
                    session,
                    self.org_id,
                    self.project_id,
                    stage_name,
                    task_id,
                    review_val,
                )
            else:

                labels = task["labels"]
                await self.context.labeling.put_labeling_results(
                    session, self.org_id, self.project_id, stage_name, task_id, labels
                )

        except Exception as error:
            print(error)
            point_error = deepcopy(task)
            point_error["error"] = error
            return point_error
        return None

    async def _put_tasks(self, stage_name: str, tasks: List[Dict]) -> List[Dict]:
        async with aiohttp.ClientSession() as session:
            coros = [self._put_task(session, stage_name, task) for task in tasks]

            temp = await gather_with_concurrency(10, coros, "Uploading tasks")
            failed = []
            for val in temp:
                if val:
                    failed.append(val)
            return failed

    def put_tasks(self, stage_name: str, tasks: List[Dict]) -> List[Dict]:
        """Put tasks, return tasks that failed."""
        return asyncio.run(self._put_tasks(stage_name, tasks))
