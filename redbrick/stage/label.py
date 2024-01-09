"""Label stage."""


from dataclasses import dataclass, field
import json
from typing import Any, Dict, Optional

from redbrick.common.stage import Stage


@dataclass
class LabelStage(Stage):
    """Label Stage.

    Parameters
    --------------
    stage_name: str
        Stage name.

    on_submit: Optional[str] = None
        The next stage for the task when submitted in current stage.
        If None, will go to Output stage.

    config: Config
        Stage config.
    """

    @dataclass
    class Config(Stage.Config):
        """Label Stage Config.

        Parameters
        --------------
        auto_assignment: Optional[bool]
            Enable task auto assignment. (Default: True)

        auto_assignment_queue_size: Optional[int]
            Task auto-assignment queue size. (Default: 5)

        show_uploaded_annotations: Optional[bool]
            Show uploaded annotations to users. (Default: True)
        """

        auto_assignment: Optional[bool] = None
        auto_assignment_queue_size: Optional[int] = None
        show_uploaded_annotations: Optional[bool] = None

        @classmethod
        def from_entity(cls, entity: Optional[Dict] = None) -> "LabelStage.Config":
            """Get object from entity."""
            if not entity:
                return cls()
            return cls(
                auto_assignment=entity.get("autoAssign"),
                auto_assignment_queue_size=entity.get("queueSize"),
                show_uploaded_annotations=None
                if entity.get("blindedAnnotation") is None
                else not entity["blindedAnnotation"],
            )

        def to_entity(self) -> Dict:
            """Get entity from object."""
            entity: Dict[str, Any] = {}
            if self.auto_assignment is not None:
                entity["autoAssign"] = self.auto_assignment
            if self.auto_assignment_queue_size is not None:
                entity["queueSize"] = self.auto_assignment_queue_size
            if self.show_uploaded_annotations is not None:
                entity["blindedAnnotation"] = not self.show_uploaded_annotations
            return entity

    stage_name: str
    on_submit: Optional[str] = None
    config: Config = field(default_factory=Config.from_entity)

    @classmethod
    def from_entity(cls, entity: Dict) -> "LabelStage":
        """Get object from entity"""
        config = entity.get("stageConfig")
        if config and isinstance(config, str):
            config = json.loads(config)
        return cls(
            stage_name=entity["stageName"],
            on_submit=entity["routing"]["nextStageName"],
            config=cls.Config.from_entity(config or {}),
        )

    def to_entity(self) -> Dict:
        """Get entity from object."""
        return {
            "brickName": "manual-labeling",
            "stageName": self.stage_name,
            "routing": {
                "nextStageName": self.on_submit or "Output",
            },
            "stageConfig": self.config.to_entity(),
        }
