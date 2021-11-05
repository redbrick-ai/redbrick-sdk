"""Template creator for the most basic projects."""

from typing import List, Dict, Tuple

OUTPUT_NAME = "Output"
LABEL_NAME = "Label"
ACTIVE_LEARNING_ENTRY = "Finalized_Tasks"
MIN_REVIEW = 0
MAX_REVIEW = 6


def _get_middle_stages(reviews: int, passed_name: str) -> Tuple[List[Dict], str]:
    """Get label and review stages."""
    label_stage = {
        "brickName": "manual-labeling",
        "stageName": LABEL_NAME,
        "routing": {
            "nextStageName": "Review_1" if reviews > 0 else passed_name,
        },
        "stageConfig": {"isPrimaryStage": True},
    }
    feedback_stage = {
        "brickName": "feedback",
        "stageName": "Failed_Review",
        "routing": {
            "feedbackStageName": label_stage["stageName"],
        },
        "stageConfig": {},
    }

    stages = [label_stage]
    for i in range(1, reviews + 1):
        stages.append(
            {
                "brickName": "expert-review",
                "stageName": f"Review_{i}",
                "stageConfig": {},
                "routing": {
                    "passed": passed_name if i == reviews else f"Review_{i+1}",
                    "failed": feedback_stage["stageName"],
                },
            }
        )

    if reviews > 0:
        stages.append(feedback_stage)

    return stages, LABEL_NAME


def _get_active_learning_config(
    middle_stages: List[Dict], entry_point: str, batch_size: int, cycle_size: int
) -> List[Dict]:

    return (
        [
            {
                "brickName": "labelset-input",
                "routing": {
                    "nextStageName": "Active_Learning",
                },
                "stageName": "Input",
                "stageConfig": {},
            },
            {
                "brickName": "active-learning",
                "routing": {
                    "passed": OUTPUT_NAME,
                    "failed": entry_point,
                },
                "stageName": "Active_Learning",
                "stageConfig": {
                    "batchSize": batch_size,
                    "cycleSize": cycle_size,
                },
            },
            {
                "brickName": "labelset-output",
                "stageName": OUTPUT_NAME,
                "routing": {
                    "nextStageName": "END",
                },
                "stageConfig": {},
            },
        ]
        + middle_stages
        + [
            {
                "brickName": "feedback",
                "stageName": ACTIVE_LEARNING_ENTRY,
                "routing": {
                    "feedbackStageName": "Active_Learning",
                },
                "stageConfig": {},
            },
        ]
    )


def get_basic_project(reviews: int = 0) -> List[Dict]:
    """Get basic project config with reviews."""
    reviews = max(reviews, MIN_REVIEW)
    reviews = min(reviews, MAX_REVIEW)

    middle_stages, entry_point = _get_middle_stages(reviews, OUTPUT_NAME)

    input_stage = {
        "brickName": "labelset-input",
        "routing": {
            "nextStageName": entry_point,
        },
        "stageName": "Input",
        "stageConfig": {},
    }
    output_stage = {
        "brickName": "labelset-output",
        "stageName": OUTPUT_NAME,
        "routing": {
            "nextStageName": "END",
        },
        "stageConfig": {},
    }

    temp = [input_stage] + middle_stages + [output_stage]

    return temp


def get_active_learning_project(
    reviews: int, batch_size: int, cycle_size: int
) -> List[Dict]:
    """Get active learning project."""
    middle_stages, entry_point = _get_middle_stages(reviews, ACTIVE_LEARNING_ENTRY)

    return _get_active_learning_config(
        middle_stages, entry_point, batch_size, cycle_size
    )
