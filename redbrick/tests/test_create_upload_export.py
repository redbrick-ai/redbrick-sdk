"""Test create project, upload labels and export data."""
import contextlib
from datetime import datetime
import os
import time
import random
from uuid import uuid4
from typing import Dict, Generator, List, Optional, Tuple
import pytest

import redbrick
from redbrick.common.enums import LabelType, StorageMethod
from redbrick.project import RBProject


@pytest.fixture(name="org_id")
def fixture_org_id() -> str:
    """Get org_id."""
    return os.environ.get("REDBRICK_SDK_ORG_ID", "17391ebc-1b0c-468e-9029-8f2308f05df5")


@pytest.fixture(name="api_key")
def fixture_api_key() -> str:
    """Get api_key."""
    return os.environ.get(
        "REDBRICK_SDK_API_KEY", "dNW-B8l1zBID2eitjZ-WtG-XYp9wChi89wMXNOvWOsQ"
    )


@pytest.fixture(name="url")
def fixture_url() -> str:
    """Get url."""
    return os.environ.get(
        "REDBRICK_SDK_URL", "https://piljxrnf0h.execute-api.us-east-1.amazonaws.com/qa"
    )


@contextlib.contextmanager
def create_test_project(
    org_id: str,
    api_key: str,
    url: str,
    project_name: str,
    label_type: LabelType,
    taxonomy: str = "DEFAULT::Berkeley Deep Drive (BDD)",
    reviews: int = 1,
) -> Generator[RBProject, None, None]:
    """Create project."""
    project: Optional[RBProject] = None
    try:
        org = redbrick.get_org(api_key=api_key, org_id=org_id, url=url)
        project = org.create_project(
            name=project_name,
            label_type=label_type,
            taxonomy_name=taxonomy,
            reviews=reviews,
        )
        yield project
    finally:
        if project:
            project.context.project.delete_project(project.org_id, project.project_id)


def upload_test_data(project: RBProject, num_tasks: int) -> None:
    """Upload test data."""
    tasks = [
        {
            "name": str(uuid4()),
            "items": ["http://datasets.redbrickai.com/bccd/BloodImage_00000.jpg"],
        }
        for _ in range(num_tasks)
    ]
    project.upload.create_datapoints(
        StorageMethod.PUBLIC,
        tasks,
    )


def get_test_label_classify() -> List[Dict]:
    """Get classify test label."""
    categories = ["bus", "bike", "truck", "motor", "car", "train", "rider"]
    return [
        {
            "labelid": str(uuid4()),
            "category": [["object", random.choice(categories)]],
            "attributes": [],
            "taskclassify": True,
        }
    ]


def get_test_label_polygon() -> List[Dict]:
    """Get polygon test label."""
    categories = ["bus", "bike", "truck", "motor", "car", "train", "rider"]
    return (
        [
            {
                "labelid": str(uuid4()),
                "category": [["object", random.choice(categories)]],
                "attributes": [],
                "polygon": [
                    {
                        "xnorm": random.random(),
                        "ynorm": random.random(),
                    }
                    for _ in range(random.randint(3, 10))
                ],
            }
            for _ in range(random.randint(1, 3))
        ]
        if random.random() > 0.5
        else []
    )


def label_test_data(
    project: RBProject, num_tasks: int
) -> Tuple[List[Dict], List[Dict]]:
    """Label test data."""
    all_tasks, labeled_tasks = [], []
    if project.project_type == LabelType.IMAGE_CLASSIFY:
        labels = get_test_label_classify
    elif project.project_type == LabelType.IMAGE_POLYGON:
        labels = get_test_label_polygon

    tasks: List[Dict] = []
    retries = 0
    while True:  # to make sure tasks have been fully processed
        tasks = project.labeling.get_tasks("Label", num_tasks)
        if len(tasks) == num_tasks:
            break
        time.sleep(1)
        retries += 1
        if retries == 10:
            assert False, tasks

    to_label = random.randint(0, num_tasks)
    cur_batch = [
        {
            "taskId": task["taskId"],
            "labels": labels(),
        }
        for task in tasks[:to_label]
    ]
    labeled_tasks.extend(cur_batch)
    all_tasks.extend(
        cur_batch
        + [
            {
                "taskId": task["taskId"],
                "labels": [],
            }
            for task in tasks[to_label:]
        ]
    )
    if cur_batch:
        project.labeling.put_tasks("Label", cur_batch)

    return all_tasks, labeled_tasks


def review_test_data(project: RBProject, labeled_tasks: List[Dict]) -> List[Dict]:
    """Review test data."""
    reviewed_tasks = []

    tasks = project.review.get_tasks("Review_1", random.randint(0, len(labeled_tasks)))

    cur_batch = [
        {
            "taskId": task["taskId"],
            "reviewVal": random.random() > 0.5,
        }
        for task in tasks
    ]
    reviewed_tasks.extend(cur_batch)
    if cur_batch:
        project.review.put_tasks("Review_1", cur_batch)

    return reviewed_tasks


def validate_redbrick_labels(tasks: Dict[str, Dict], exported: List[Dict]) -> None:
    """Validate redbrick labels."""
    for task in exported:
        assert (
            task["taskId"] in tasks
            and tasks[task["taskId"]]["labels"] == task["labels"]
        )


def validate_export_data_redbrick(
    project: RBProject, tasks: Dict[str, Dict], groundtruth_task_ids: List[str]
) -> None:
    """Export and validate test data for redbrick format."""
    # All tasks
    exported_data = project.export.redbrick_format(False)
    assert set({task["taskId"] for task in exported_data}) == set(tasks.keys())
    validate_redbrick_labels(tasks, exported_data)

    # Groundtruth
    exported_data = project.export.redbrick_format()
    assert set({task["taskId"] for task in exported_data}) == set(groundtruth_task_ids)
    validate_redbrick_labels(tasks, exported_data)

    # TaskId
    task_id = random.choice(list(tasks.keys()))
    exported_data = project.export.redbrick_format(task_id=task_id)
    assert set({task["taskId"] for task in exported_data}) == set([task_id])
    validate_redbrick_labels(tasks, exported_data)


def validate_coco_labels(tasks: Dict[str, Dict], exported: Dict) -> None:
    """Validate coco labels."""
    pass


def validate_export_data_coco(
    project: RBProject, tasks: Dict[str, Dict], groundtruth_task_ids: List[str]
) -> None:
    """Export and validate test data for coco format."""
    # All tasks
    exported_data = project.export.coco_format(False)
    assert len(exported_data["images"]) == len(tasks)
    validate_coco_labels(tasks, exported_data)

    # Groundtruth
    exported_data = project.export.coco_format()
    assert len(exported_data["images"]) == len(groundtruth_task_ids)
    validate_coco_labels(tasks, exported_data)

    # TaskId
    task_id = random.choice(list(tasks.keys()))
    exported_data = project.export.coco_format(task_id=task_id)
    assert len(exported_data) == 1
    validate_coco_labels(tasks, exported_data)


@pytest.mark.slow
@pytest.mark.parametrize(
    "label_type", (LabelType.IMAGE_CLASSIFY, LabelType.IMAGE_POLYGON)
)
def test_classify_project(
    org_id: str, api_key: str, url: str, label_type: LabelType
) -> None:
    """Test export."""
    project_name = (
        f"test-{label_type.value}-{datetime.strftime(datetime.now(), '%Y%m%d%H%M%S')}"
    )
    with create_test_project(org_id, api_key, url, project_name, label_type) as project:

        task_count = 20
        upload_test_data(project, task_count)

        all_tasks, labeled_tasks = label_test_data(project, task_count)

        reviewed_tasks = review_test_data(project, labeled_tasks)

        tasks_map = {task["taskId"]: task for task in all_tasks}
        groundtruth_task_ids = [
            task["taskId"] for task in reviewed_tasks if task["reviewVal"]
        ]

        validate_export_data_redbrick(project, tasks_map, groundtruth_task_ids)
        validate_export_data_coco(project, tasks_map, groundtruth_task_ids)
