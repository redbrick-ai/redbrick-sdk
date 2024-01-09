"""RedBrick project stages."""
from typing import Dict, List

from redbrick.common.stage import Stage
from redbrick.stage.label import LabelStage
from redbrick.stage.review import ReviewStage
from redbrick.stage.model import ModelStage


def get_middle_stages(reviews: int) -> List[Stage]:
    """Get label and review stages."""
    reviews = min(max(reviews, 0), 6)
    stages: List[Stage] = []
    stages.append(LabelStage(stage_name="Label"))
    prev_stage = stages[0]

    for i in range(1, reviews + 1):
        stage = ReviewStage(stage_name=f"Review_{i}", on_reject=stages[0].stage_name)
        stages.append(stage)
        if isinstance(prev_stage, LabelStage):
            prev_stage.on_submit = stage.stage_name
        elif isinstance(prev_stage, ReviewStage):
            prev_stage.on_accept = stage.stage_name
        prev_stage = stage

    return stages


def get_project_stages(stages: List[Stage]) -> List[Dict]:
    """Get project stage config."""
    input_stage = {
        "brickName": "labelset-input",
        "stageName": "Input",
        "routing": {
            "nextStageName": stages[0].stage_name if stages else "Output",
        },
        "stageConfig": {},
    }
    output_stage = {
        "brickName": "labelset-output",
        "stageName": "Output",
        "routing": {
            "nextStageName": "END",
        },
        "stageConfig": {},
    }

    stage_configs: List[Dict] = []
    feedback_stages: List[Dict] = []

    for stage in stages:
        stage_configs.append(stage.to_entity())
        if isinstance(stage, ReviewStage):
            if not any(
                review_feedback_stage["routing"]["feedbackStageName"]
                == stage_configs[-1]["routing"]["failed"]
                for review_feedback_stage in feedback_stages
            ):
                feedback_stages.append(
                    {
                        "brickName": "feedback",
                        "stageName": f"Failed_Review_{len(feedback_stages) + 1}",
                        "routing": {
                            "feedbackStageName": stage_configs[-1]["routing"]["failed"],
                        },
                        "stageConfig": {},
                    }
                )

            stage_configs[-1]["routing"]["failed"] = next(
                review_feedback_stage
                for review_feedback_stage in feedback_stages
                if review_feedback_stage["routing"]["feedbackStageName"]
                == stage_configs[-1]["routing"]["failed"]
            )["stageName"]

    return [input_stage] + stage_configs + feedback_stages + [output_stage]
