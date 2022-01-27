"""Main object for RedBrick SDK."""
import os
import json
from datetime import datetime
from configparser import ConfigParser
from typing import Dict, List, Optional, Tuple, no_type_check
from uuid import uuid4

from InquirerPy import inquirer  # type: ignore

from redbrick.common.context import RBContext
from redbrick.project import RBProject
from redbrick.utils.logging import print_error, print_info
from redbrick.utils.files import download_files


# pylint: skip-file


class RBSlicer:
    """Interact with a RedBrick task in 3D Slicer application."""

    def __init__(
        self, context: RBContext, region: str, client_id: str, url: str
    ) -> None:
        """Construct RBProject."""
        self.context = context
        self.region = region
        self.client_id = client_id
        self.url = url

        self.username: Optional[str] = None
        self.auth_token: Optional[str] = None
        self.project: Optional[RBProject] = None

        self.segments: List[str] = []

    def authenticate_user(self) -> Tuple[str, str]:
        """Authenticate user and get username and auth token."""
        import tenacity
        import boto3  # type: ignore

        config_file = os.path.join(os.path.expanduser("~"), ".redbrickai", "token")
        config = ConfigParser()
        config.read(config_file)
        if (
            "token" in config
            and "uname" in config["token"]
            and "value" in config["token"]
            and "time" in config["token"]
            and int(config["token"]["time"]) >= int(datetime.now().timestamp()) + 3600
        ):
            return config["token"]["uname"], config["token"]["value"]

        client = boto3.client("cognito-idp", region_name=self.region)
        uname = ""
        try:
            for attempt in tenacity.Retrying(
                reraise=True,
                stop=tenacity.stop_after_attempt(3),
                retry=tenacity.retry_if_not_exception_type((KeyboardInterrupt,)),
            ):
                with attempt:
                    uname = inquirer.text(message="Username:", default=uname).execute()
                    psswd = inquirer.text(message="Password:").execute()
                    response = client.initiate_auth(
                        ClientId=self.client_id,
                        AuthFlow="USER_PASSWORD_AUTH",
                        AuthParameters={"USERNAME": uname, "PASSWORD": psswd},
                    )
                    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
        except tenacity.RetryError as error:
            raise Exception("Failed to authenticate") from error

        config["token"] = {
            "uname": uname,
            "time": int(datetime.now().timestamp())
            + response["AuthenticationResult"]["ExpiresIn"],
            "value": response["AuthenticationResult"]["AccessToken"],
        }

        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, "w", encoding="utf-8") as file_:
            config.write(file_)

        return config["token"]["uname"], config["token"]["value"]

    def logout(self) -> None:
        """Logout current session and delete token file."""
        config_file = os.path.join(os.path.expanduser("~"), ".redbrickai", "token")
        if os.path.isfile(config_file):
            os.remove(config_file)
        self.username = None
        self.auth_token = None

    @staticmethod
    def _get_categories(category: Dict) -> List[str]:
        category_names = [category["name"]]
        for child in category.get("children", []):
            category_names += [
                category_names[0] + "::" + name
                for name in RBSlicer._get_categories(child)
            ]
        return category_names

    @no_type_check
    def get_task(
        self, org_id: str, project_id: str, task_id: str, stage_name: str
    ) -> None:
        """Get task for labeling."""
        self.username, self.auth_token = self.authenticate_user()

        self.context.client.auth_token = self.auth_token

        if not self.project:
            self.project = RBProject(self.context, org_id, project_id)

        tasks, taxonomy = self.project.export._get_raw_data_single(task_id=task_id)

        assert len(tasks) == 1, "Task not available"

        task = tasks[0]
        parent_cat = taxonomy.get("categories", [])
        if len(parent_cat) == 1 and parent_cat[0]["name"] == "object":
            for child in parent_cat[0]["children"]:
                self.segments += RBSlicer._get_categories(child)

        slicer.mrmlScene.Clear(0)

        root = os.path.join(os.path.expanduser("~"), ".redbrick-slicer")
        org_dir = os.path.join(root, str(org_id))
        project_dir = os.path.join(org_dir, str(project_id))
        task_dir = os.path.join(project_dir, str(task_id))

        data_dir = os.path.join(task_dir, "data")
        os.makedirs(data_dir, exist_ok=True)

        files = []
        for idx, item in enumerate(task["itemsPresigned"]):
            path = os.path.join(data_dir, f"{idx}.dcm")
            if not os.path.isfile(path):
                files.append((item, path))

        download_files(files)

        with DICOMUtils.TemporaryDICOMDatabase() as db:
            DICOMUtils.importDicom(data_dir, db)
            patientUIDs = db.patients()
            assert len(patientUIDs) == 1, "Failed to load data"
            DICOMUtils.loadPatientByUID(patientUIDs[0])

        if task["labelsPath"]:
            labels_path = os.path.join(task_dir, "labels.nii")
            download_files([(task["labelsPath"], labels_path)])
            loadSegmentation(labels_path)
            segmentationNode = slicer.mrmlScene.GetFirstNodeByClass(
                "vtkMRMLSegmentationNode"
            )

        else:
            segmentationNode = slicer.vtkMRMLSegmentationNode()
            slicer.mrmlScene.AddNode(segmentationNode)

        selectModule("SegmentEditor")
        segmentationNode = slicer.mrmlScene.GetFirstNodeByClass(
            "vtkMRMLSegmentationNode"
        )

        rb_segmentation = segmentationNode.GetSegmentation()
        labels = json.loads(task["labelsData"])
        label_rb_map = {}
        for label in labels:
            label_rb_map[label["dicom"]["instanceid"]] = "::".join(
                label["category"][0][1:]
            )

        display = segmentationNode.GetDisplayNode()
        for num in range(rb_segmentation.GetNumberOfSegments()):
            seg = rb_segmentation.GetNthSegment(num)
            display.SetSegmentVisibility(rb_segmentation.GetNthSegmentID(num), True)
            val = seg.GetLabelValue()
            if val in label_rb_map:
                seg.SetName(label_rb_map[val])

        self.project.labeling.assign_task(stage_name, task_id, self.username)

        while True:
            user_val = inquirer.rawlist("Choice:", ["Save", "Submit", "Exit"]).execute()
            if user_val == "Save":
                self.save_data(task_id, stage_name, False)
                print_info("Saved")
            elif user_val.strip() == "2":
                self.save_data(task_id, stage_name, True)
                print_info("Submitted")
                break
            else:
                slicer.mrmlScene.Clear(0)
                break

    @no_type_check
    def save_data(
        self,
        task_id: str,
        stage_name: str,
        finished: bool = False,
    ) -> None:
        """Save data for task."""
        import numpy as np
        import nibabel as nb  # type: ignore

        root = os.path.join(os.path.expanduser("~"), ".redbrick-slicer")
        scene = slicer.mrmlScene
        segmentationNode = scene.GetFirstNodeByClass("vtkMRMLSegmentationNode")
        referenceVolumeNode = scene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
        labelmapVolumeNode = scene.AddNewNodeByClass("vtkMRMLLabelMapVolumeNode")
        slicer.modules.segmentations.logic().ExportVisibleSegmentsToLabelmapNode(
            segmentationNode, labelmapVolumeNode, referenceVolumeNode
        )
        new_labels = os.path.join(root, "new_labels.nii")
        slicer.util.saveNode(labelmapVolumeNode, new_labels)
        scene.RemoveNode(labelmapVolumeNode.GetDisplayNode().GetColorNode())
        scene.RemoveNode(labelmapVolumeNode)

        img = nb.load(new_labels)
        img.set_data_dtype(np.ubyte)
        data = np.round(img.get_fdata()).astype(np.ubyte)
        means = nb.Nifti1Image(data, header=img.header, affine=img.affine)

        segmentationNode = scene.GetFirstNodeByClass("vtkMRMLSegmentationNode")
        rb_segmentation = segmentationNode.GetSegmentation()
        labels = []
        for num in range(rb_segmentation.GetNumberOfSegments()):
            seg = rb_segmentation.GetNthSegment(num)
            name = seg.GetName()
            if name not in self.segments:
                print_error(f"Category: `{name}` not found. Skipping")
                return
            labels.append(
                {
                    "category": [["object"] + name.split("::")],
                    "attributes": [],
                    "labelid": str(uuid4()),
                    "dicom": {"instanceid": seg.GetLabelValue()},
                }
            )

        self.project.labeling.put_tasks(
            stage_name,
            [
                {
                    "taskId": task_id,
                    "labelBlob": means.to_bytes(),
                    "draft": not finished,
                    "labels": labels,
                }
            ],
        )

        if finished:
            scene.Clear(0)
