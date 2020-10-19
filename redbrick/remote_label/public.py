"""Public interface to remote_label."""
from redbrick.api import RedBrickApi
import json
from redbrick.entity.task import Task
from redbrick.entity.label import ImageBoundingBox, VideoBoundingBox
from typing import List, Union


class RemoteLabel:
    """An interface to RemoteLabel brick."""

    def __init__(self, org_id: str, project_id: str, stage_name: str) -> None:
        """Construct RemoteLabel instance."""
        self.org_id = org_id
        self.project_id = project_id
        self.stage_name = stage_name
        self.api_client = RedBrickApi(cache=False)

    def cache_tasks(self):
        """Get the remote labeling task(s) and cache the data."""
        pass

    def get_num_tasks(self):
        """Get the number of tasks queued."""
        num = self.api_client.get_num_remote_tasks(
            org_id=self.org_id, project_id=self.project_id, stage_name=self.stage_name
        )
        return num

    def get_task(self, num_tasks: int) -> Task:
        """User facing function to get task."""
        task = self.__get_remote_labeling_task(num_tasks=num_tasks)
        return task

    def submit_task(
        self, task: Task, labels: Union[ImageBoundingBox, VideoBoundingBox]
    ):
        """User facing funciton to submit a task."""
        new_subname = "remote-labeling"

        # Check label type
        if task.task_data_type == "IMAGE_BBOX":
            if not isinstance(labels, ImageBoundingBox):
                raise ValueError("Labels must be of type ImageBoundingBox!")
        if task.task_data_type == "VIDEO_BBOX":
            if not isinstance(labels, VideoBoundingBox):
                raise ValueError("Labels must be of type VideoBoundingBox!")

        # Put task data
        self.__put_task_data(
            dp_id=task.dp_id,
            sub_name=new_subname,
            task_data=labels,
            taxonomy_name=task.taxonomy["name"],
            taxonomy_version=task.taxonomy["version"],
            td_type=task.task_data_type,
        )

        # Put remote labeling task
        submit_task = Task(
            org_id=task.org_id,
            project_id=task.project_id,
            stage_name=task.stage_name,
            task_id=task.task_id,
            dp_id=task.dp_id,
            sub_name=new_subname,
            taxonomy=task.taxonomy,
            items_list=task.items_list,
            items_list_presigned=task.items_list_presigned,
            task_data_type=task.task_data_type,
        )
        self.__put_remote_labeling_task(submit_task)

    def __put_task_data(
        self,
        dp_id: str,
        sub_name: str,
        task_data: Union[ImageBoundingBox, VideoBoundingBox],
        taxonomy_name: str,
        taxonomy_version: str,
        td_type: str,
    ):
        """Read labels from local folder, and submit the labels."""
        task_datas = str(task_data)  # Stringify the json object

        res = self.api_client.putTaskData(
            org_id=self.org_id,
            project_id=self.project_id,
            dp_id=dp_id,
            stage_name=self.stage_name,
            sub_name=sub_name,
            task_data=task_datas,
            taxonomy_name=taxonomy_name,
            taxonomy_version=taxonomy_version,
            td_type=td_type,
        )
        return res

    def __put_remote_labeling_task(self, task: Task):
        """Put the remote labeling task to the backend."""
        finishedTask = {
            "orgId": task.org_id,
            "projectId": task.project_id,
            "stageName": task.stage_name,
            "taskId": task.task_id,
            "newSubName": task.sub_name,
        }
        res = self.api_client.putRemoteLabelingTask(finishedTask)
        return res

    def __get_remote_labeling_task(self, num_tasks: int) -> Task:
        """Get the labeling tasks from API."""
        task = self.api_client.tasksToLabelRemote(
            orgId=self.org_id,
            projectId=self.project_id,
            stageName=self.stage_name,
            numTasks=num_tasks,
        )
        return task
