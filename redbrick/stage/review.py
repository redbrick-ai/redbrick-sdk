"""Review stage."""

from dataclasses import dataclass, field
import json
from typing import Any, Dict, Optional, Union

from redbrick.common.stage import Stage


@dataclass
class ReviewStage(Stage):
    """Review Stage.

    Parameters
    --------------
    stage_name: str
        Stage name.

    on_accept: Union[bool, str] = True
        The next stage for the task when accepted in current stage.
        If True, the task will go to ground truth.
        If False, the task will be archived.

    on_reject: Union[bool, str] = False
        The next stage for the task when rejected in current stage.
        If True, the task will go to ground truth.
        If False, the task will be archived.

    config: Config = Config()
        Stage config.
    """

    @dataclass
    class Config(Stage.Config):
        """Review Stage Config.

        Parameters
        --------------
        review_percentage: Optional[float]
            Percentage of tasks in [0, 1] that will be sampled for review. (Default: 1)

        auto_assignment: Optional[bool]
            Enable task auto assignment. (Default: True)

        auto_assignment_queue_size: Optional[int]
            Task auto-assignment queue size. (Default: 5)
        """

        review_percentage: Optional[float] = None
        auto_assignment: Optional[bool] = None
        auto_assignment_queue_size: Optional[int] = None

        @classmethod
        def from_entity(cls, entity: Optional[Dict] = None) -> "ReviewStage.Config":
            """Get object from entity."""
            if not entity:
                return cls()
            return cls(
                review_percentage=entity.get("reviewPercent"),
                auto_assignment=entity.get("autoAssign"),
                auto_assignment_queue_size=entity.get("queueSize"),
            )

        def to_entity(self) -> Dict:
            """Get entity from object."""
            entity: Dict[str, Any] = {}
            if self.review_percentage is not None:
                entity["reviewPercent"] = self.review_percentage
            if self.auto_assignment is not None:
                entity["autoAssign"] = self.auto_assignment
            if self.auto_assignment_queue_size is not None:
                entity["queueSize"] = self.auto_assignment_queue_size
            return entity

    stage_name: str
    on_accept: Union[bool, str] = True
    on_reject: Union[bool, str] = False
    config: Config = field(default_factory=Config.from_entity)

    @classmethod
    def from_entity(cls, entity: Dict) -> "ReviewStage":
        """Get object from entity"""
        config = entity.get("stageConfig")
        if config and isinstance(config, str):
            config = json.loads(config)
        return cls(
            stage_name=entity["stageName"],
            on_accept=entity["routing"]["passed"],
            on_reject=entity["routing"]["failed"],
            config=cls.Config.from_entity(config or {}),
        )

    def to_entity(self) -> Dict:
        """Get entity from object."""
        return {
            "brickName": "expert-review",
            "stageName": self.stage_name,
            "routing": {
                "passed": self.get_next_stage(self.on_accept),
                "failed": self.get_next_stage(self.on_reject),
            },
            "stageConfig": self.config.to_entity(),
        }
