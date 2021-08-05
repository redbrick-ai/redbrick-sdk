"""Template creator for the most basic projects."""

from typing import List, Dict, Tuple

OUTPUT_NAME = "Output"
LABEL_NAME = "Label"
MIN_REVIEW = 0
MAX_REVIEW = 6


def _get_middle_stages(reviews: int, passed_name: str) -> Tuple[List[Dict], str]:
    """Get label and review stages."""
    label_stage = {
        "brickName": "manual-labeling",
        "stageName": LABEL_NAME,
        "routing": {"nextStageName": "Review_1" if reviews > 0 else passed_name,},
        "stageConfig": {},
    }
    feedback_stage = {
        "brickName": "feedback",
        "stageName": "Failed_Review",
        "routing": {"feedbackStageName": label_stage["stageName"],},
        "stageConfig": {},
    }

    stages = [label_stage]
    for ii in range(1, reviews + 1):
        stages.append(
            {
                "brickName": "expert-review",
                "stageName": f"Review_{ii}",
                "stageConfig": {},
                "routing": {
                    "passed": passed_name if ii == reviews else f"Review_{ii+1}",
                    "failed": feedback_stage["stageName"],
                },
            }
        )

    if reviews > 0:
        stages.append(feedback_stage)

    return stages, LABEL_NAME


def get_basic_project(reviews: int = 0) -> List[Dict]:
    """Get basic project config with reviews."""
    if reviews < MIN_REVIEW:
        reviews = MIN_REVIEW
    if reviews > MAX_REVIEW:
        reviews = MAX_REVIEW

    middle_stages, entry_point = _get_middle_stages(reviews, OUTPUT_NAME)

    input_stage = {
        "brickName": "labelset-input",
        "routing": {"nextStageName": entry_point,},
        "stageName": "Input",
        "stageConfig": {},
    }
    output_stage = {
        "brickName": "labelset-output",
        "stageName": OUTPUT_NAME,
        "routing": {"nextStageName": "END",},
        "stageConfig": {},
    }

    temp = [input_stage] + middle_stages + [output_stage]

    return temp
