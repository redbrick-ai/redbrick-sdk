"""Test CLI export."""
import contextlib
from datetime import datetime
import os
import json
import pickle
import shutil
import random
import subprocess
from uuid import uuid4
from typing import Generator, Optional, Tuple

import pytest
import tenacity

from redbrick.common.enums import LabelType, StorageMethod
from redbrick.project import RBProject


@contextlib.contextmanager
def create_project(
    org_id: str,
    api_key: str,
    url: str,
    label_type: LabelType,
    taxonomy: str = "Berkeley Deep Drive (BDD)",
    reviews: int = 1,
) -> Generator[Tuple[str, RBProject], None, None]:
    """Create project."""
    profile = datetime.strftime(datetime.now(), "%Y%m%d%H%M%S%f") + str(
        random.randint(0, 1000)
    )
    project_name = f"cli-{profile}"
    home_dir = os.path.expanduser("~")
    project_dir = os.path.join(home_dir, project_name)
    project: Optional[RBProject] = None
    try:
        os.makedirs(project_dir)
        subprocess.run(
            [
                "redbrick",
                "config",
                "add",
                "-o",
                org_id,
                "-k",
                api_key,
                "-u",
                url,
                "-p",
                profile,
            ],
            check=True,
        )
        subprocess.run(["redbrick", "config", "set", profile], check=True)
        subprocess.run(
            [
                "redbrick",
                "init",
                "-n",
                project_name,
                "-t",
                taxonomy,
                "-l",
                label_type.value,
                "-r",
                str(reviews),
                project_dir,
            ],
            check=True,
        )

        cache_name = os.listdir(os.path.join(project_dir, ".redbrick", "cache"))
        with open(
            os.path.join(
                project_dir, ".redbrick", "cache", cache_name[0], "project.pickle"
            ),
            "rb",
        ) as file_:
            project = pickle.load(file_)

        assert project
        yield project_dir, project
    finally:
        os.chdir(home_dir)
        shutil.rmtree(project_dir, ignore_errors=True)
        if project:
            project.context.project.delete_project(project.org_id, project.project_id)
        if os.environ.get("REDBRICK_SDK_SOURCE") == "GITHUB":
            subprocess.run(["redbrick", "config", "clear"], check=True)
        else:
            subprocess.run(["redbrick", "config", "remove", profile], check=True)


def upload_data(project: RBProject, num_tasks: int) -> None:
    """Upload data."""
    project.upload.create_datapoints(
        StorageMethod.PUBLIC,
        [
            {
                "name": str(uuid4()),
                "items": ["http://datasets.redbrickai.com/bccd/BloodImage_00000.jpg"],
            }
            for _ in range(num_tasks)
        ],
    )


def label_data(project: RBProject, num_tasks: int) -> None:
    """Label data."""
    categories = ["bus", "bike", "truck", "motor", "car", "train", "rider"]
    while num_tasks:
        for attempt in tenacity.Retrying(
            reraise=True,
            stop=tenacity.stop_after_attempt(10),
            wait=tenacity.wait_exponential(multiplier=1, min=1, max=10),
            retry=tenacity.retry_if_not_exception_type(
                (KeyboardInterrupt, PermissionError, ValueError)
            ),
        ):
            with attempt:
                tasks = project.labeling.get_tasks("Label", num_tasks)
                assert tasks
        num_tasks -= len(tasks)
        project.labeling.put_tasks(
            "Label",
            [
                {
                    **task,
                    "labels": [
                        {
                            "category": [["object", random.choice(categories)]],
                            "attributes": [],
                            "polygon": [
                                {
                                    "xnorm": random.random(),
                                    "ynorm": random.random(),
                                }
                                for _ in range(random.randint(3, 10))
                            ],
                            "labelid": str(uuid4()),
                        }
                        for _ in range(random.randint(1, 3))
                    ],
                }
                for task in tasks
            ],
        )


@pytest.mark.slow
def test_cli_export(org_id: str, api_key: str, url: str) -> None:
    """Test cli export."""
    with create_project(org_id, api_key, url, LabelType.IMAGE_POLYGON) as (
        project_dir,
        project,
    ):
        os.chdir(project_dir)

        total_tasks = 40
        upload_data(project, total_tasks)

        files = set(os.listdir(project_dir))
        task_count = [0, 1, total_tasks // 10, total_tasks // 5, total_tasks // 2]

        labeled = 0
        for count in task_count:
            label_data(project, count)
            labeled += count
            subprocess.run(["redbrick", "export"], check=True)
            new_files = set(os.listdir(project_dir))

            with open(
                os.path.join(project_dir, list(new_files - files)[0]),
                "r",
                encoding="utf-8",
            ) as file_:
                tasks = json.load(file_)

            assert sum([1 if task["labels"] else 0 for task in tasks]) == labeled

            files = new_files
