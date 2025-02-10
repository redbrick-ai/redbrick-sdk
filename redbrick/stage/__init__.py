"""RedBrick project stages."""

from typing import Any, Dict, List, Optional, Sequence, Type

from redbrick.common.stage import Stage
from redbrick.stage.label import LabelStage
from redbrick.stage.review import ReviewStage
from redbrick.stage.model import ModelStage
from redbrick.types.taxonomy import Taxonomy


def get_middle_stages(
    reviews: int,
    consensus_settings: Optional[Dict[str, Any]] = None,
) -> List[Stage]:
    """Get label and review stages."""
    is_consensus_enabled = bool((consensus_settings or {}).get("enabled"))
    reviews = min(max(reviews, 0), 6)
    stages: List[Stage] = []
    stages.append(
        LabelStage(
            stage_name="Consensus_Label" if is_consensus_enabled else "Label",
            config=LabelStage.Config(
                is_consensus_label=True if is_consensus_enabled else None
            ),
        )
    )
    prev_stage = stages[0]

    for i in range(1, reviews + 1):
        stage = ReviewStage(
            stage_name=(
                "Consensus_Best" if i == 1 and is_consensus_enabled else f"Review_{i}"
            ),
            on_reject=stages[0].stage_name,
            config=ReviewStage.Config(
                is_consensus_merge=True if i == 1 and is_consensus_enabled else None
            ),
        )
        stages.append(stage)
        if isinstance(prev_stage, LabelStage):
            prev_stage.on_submit = stage.stage_name
        elif isinstance(prev_stage, ReviewStage):
            prev_stage.on_accept = stage.stage_name
        prev_stage = stage

    return stages


def get_project_stages(
    stages: Sequence[Stage], taxonomy: Optional[Taxonomy] = None
) -> List[Dict]:
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
        stage_configs.append(stage.to_entity(taxonomy))
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


def get_stage_object(
    stage: Dict, taxonomy: Optional[Taxonomy] = None
) -> Optional[Stage]:
    """Get stage object."""
    brick_map: Dict[str, Type[Stage]] = {
        LabelStage.BRICK_NAME: LabelStage,
        ReviewStage.BRICK_NAME: ReviewStage,
        ModelStage.BRICK_NAME: ModelStage,
    }
    return (
        brick_map[stage["brickName"]].from_entity(stage, taxonomy)
        if stage["brickName"] in brick_map
        else None
    )


def get_stage_objects(
    stages: List[Dict], taxonomy: Optional[Taxonomy] = None
) -> List[Stage]:
    """Get stage objects."""
    stage_objects = [get_stage_object(stage, taxonomy) for stage in stages]
    return [stage_object for stage_object in stage_objects if stage_object]
