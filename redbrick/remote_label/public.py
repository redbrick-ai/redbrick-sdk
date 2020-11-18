"""Public interface to remote_label."""
from typing import List, Union
from termcolor import colored
from redbrick.api import RedBrickApi
from redbrick.entity.task import Task
from redbrick.entity.label import ImageBoundingBox, VideoBoundingBox, VideoClassify
from redbrick.entity.taxonomy2 import Taxonomy2


class RemoteLabel:
    """An interface to RemoteLabel brick."""

    def __init__(self, org_id: str, project_id: str, stage_name: str) -> None:
        """Construct RemoteLabel instance."""
        print(colored("[INFO]:", "blue"), "Initializing remote-labeling module...")
        self.org_id = org_id
        self.project_id = project_id
        self.stage_name = stage_name
        self.api_client = RedBrickApi(cache=False)

        # Gather stage information and store
        stage_info = self.api_client.get_stage(
            org_id=org_id, project_id=project_id, stage_name=stage_name
        )
        taxonomy = self.api_client.get_taxonomy(
            orgId=org_id,
            name=stage_info["outputTaxonomyName"],
            version=stage_info["outputTaxonomyVersion"],
        )
        self.taxonomy: Taxonomy2 = taxonomy
        self.task_type = stage_info["outputType"]

    def get_num_tasks(self) -> int:
        """Get the number of tasks queued."""
        num = self.api_client.get_num_remote_tasks(
            org_id=self.org_id, project_id=self.project_id, stage_name=self.stage_name
        )
        return num

    def get_task(self, num_tasks: int) -> List[Task]:
        """User facing function to get task."""
        print(colored("[INFO]:", "blue"), "Retrieving task from backend...", end=" ")
        task = self.__get_remote_labeling_task(num_tasks=num_tasks)
        if len(task) == 0:
            print(colored("\n[WARNING]:", "yellow"), "No more tasks in this stage.")
            return task
        print(colored("Done.", "green"))
        return task

    def submit_task(
        self,
        task: Task,
        labels: Union[ImageBoundingBox, VideoBoundingBox, VideoClassify],
    ) -> None:
        """User facing funciton to submit a task."""
        print(colored("[INFO]", "blue"), "Submitting task to backend...", end=" ")
        new_subname = "remote-labeling"

        # Check that label category matches taxonomy
        check, classname = labels.compare_taxonomy(taxonomy=self.taxonomy)
        if not check:
            raise ValueError(
                "%s is not a valid category for taxonomy %s"
                % (classname, self.taxonomy.name)
            )

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

        print(colored("Done.", "green"))

    def __put_task_data(
        self,
        dp_id: str,
        sub_name: str,
        task_data: Union[ImageBoundingBox, VideoBoundingBox, VideoClassify],
        taxonomy_name: str,
        taxonomy_version: str,
        td_type: str,
    ) -> None:
        """Read labels from local folder, and submit the labels."""
        task_datas = str(task_data)  # Stringify the json object

        self.api_client.putTaskData(
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

    def __put_remote_labeling_task(self, task: Task) -> None:
        """Put the remote labeling task to the backend."""
        finished_task = {
            "orgId": task.org_id,
            "projectId": task.project_id,
            "stageName": task.stage_name,
            "taskId": task.task_id,
            "newSubName": task.sub_name,
        }
        self.api_client.putRemoteLabelingTask(finished_task)

    def __get_remote_labeling_task(self, num_tasks: int) -> List[Task]:
        """Get the labeling tasks from API."""
        task = self.api_client.tasksToLabelRemote(
            orgId=self.org_id,
            projectId=self.project_id,
            stageName=self.stage_name,
            numTasks=num_tasks,
        )
        return task
