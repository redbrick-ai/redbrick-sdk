"""RedBrick project stages."""
from copy import deepcopy
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class Stage:
    """Base stage."""

    class Config:
        """Stage config."""

        @classmethod
        def config_factory(cls) -> "Stage.Config":
            """Get an instance of class."""
            return cls()

    stage_name: str
    config: Config


@dataclass
class LabelStage(Stage):
    """Label Stage Config.

    Parameters
    --------------
    stage_name: str
        Stage name

    on_submit: Optional[str]
        The next stage for the task when submitted in current stage.
        If None, will go to Output stage.

    config: Config
        Stage config.
    """

    class Config(Stage.Config):
        """Label Stage Config.

        Parameters
        --------------
        auto_assignment: bool
            Enable task auto assignment. (Default: True)

        auto_assignment_queue_size: int
            Task auto-assignment queue size. (Default: 5)

        show_uploaded_annotations: bool
            Show uploaded annotations to users. (Default: True)
        """

        auto_assignment: Optional[bool] = None
        auto_assignment_queue_size: Optional[int] = None
        show_uploaded_annotations: Optional[bool] = None

        @classmethod
        def config_factory(cls) -> "LabelStage.Config":
            """Get an instance of class."""
            return cls()

    stage_name: str
    on_submit: Optional[str] = None
    config: Config = field(default_factory=Config.config_factory)


@dataclass
class ReviewStage(Stage):
    """Review Stage Config.

    Parameters
    --------------
    stage_name: str
        Stage name.


    on_accept: Optional[str] = None
        The next stage for the task when accepted in current stage.
        If None, will go to Output stage.

    on_reject: Optional[str] = None
        The next stage for the task when rejected in current stage.
        If None, will go to Output Stage.

    config: Config
        Stage config.
    """

    class Config(Stage.Config):
        """Review Stage Config.

        Parameters
        --------------
        review_percentage: float
            Percentage of tasks in [0, 1] that will be sampled for review. (Default: 1)

        auto_assignment: bool
            Enable task auto assignment. (Default: True)

        auto_assignment_queue_size: int
            Task auto-assignment queue size. (Default: 5)
        """

        review_percentage: Optional[float] = None
        auto_assignment: Optional[bool] = None
        auto_assignment_queue_size: Optional[int] = None

        @classmethod
        def config_factory(cls) -> "ReviewStage.Config":
            """Get an instance of class."""
            return cls()

    stage_name: str
    on_accept: Optional[str] = None
    on_reject: Optional[str] = None
    config: Config = field(default_factory=Config.config_factory)


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
    review_feedback_stages: List[Dict] = []
    config: Dict[str, Any] = {}

    for stage in stages:
        if isinstance(stage, LabelStage):
            if stage.config.auto_assignment is not None:
                config["autoAssign"] = stage.config.auto_assignment
            if stage.config.auto_assignment_queue_size is not None:
                config["queueSize"] = stage.config.auto_assignment_queue_size
            if stage.config.show_uploaded_annotations is not None:
                config["blindedAnnotation"] = not stage.config.show_uploaded_annotations
            stage_configs.append(
                {
                    "brickName": "manual-labeling",
                    "stageName": stage.stage_name,
                    "routing": {
                        "nextStageName": stage.on_submit or "Output",
                    },
                    "stageConfig": deepcopy(config),
                }
            )
        elif isinstance(stage, ReviewStage):
            feedback_stage = stage.on_reject or "Output"
            if not any(
                review_feedback_stage["routing"]["feedbackStageName"] == feedback_stage
                for review_feedback_stage in review_feedback_stages
            ):
                review_feedback_stages.append(
                    {
                        "brickName": "feedback",
                        "stageName": f"Failed_Review_{len(review_feedback_stages) + 1}",
                        "routing": {
                            "feedbackStageName": feedback_stage,
                        },
                        "stageConfig": {},
                    }
                )
            config.clear()
            if stage.config.review_percentage is not None:
                config["reviewPercent"] = stage.config.review_percentage
            if stage.config.auto_assignment is not None:
                config["autoAssign"] = stage.config.auto_assignment
            if stage.config.auto_assignment_queue_size is not None:
                config["queueSize"] = stage.config.auto_assignment_queue_size
            stage_configs.append(
                {
                    "brickName": "expert-review",
                    "stageName": stage.stage_name,
                    "routing": {
                        "passed": stage.on_accept or "Output",
                        "failed": next(
                            review_feedback_stage
                            for review_feedback_stage in review_feedback_stages
                            if review_feedback_stage["routing"]["feedbackStageName"]
                            == feedback_stage
                        )["stageName"],
                    },
                    "stageConfig": deepcopy(config),
                }
            )

    return [input_stage] + stage_configs + review_feedback_stages + [output_stage]
