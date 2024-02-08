"""Model stage."""

from dataclasses import dataclass, field
import json
from typing import Any, Dict, List, Optional, TypedDict, Union

from redbrick.common.stage import Stage


class ModelTaxonomyMap(TypedDict):
    """Model taxonomy map."""

    category: str
    classid: int


@dataclass
class ModelStage(Stage):
    """Model Stage.

    Parameters
    --------------
    stage_name: str
        Stage name.

    on_submit: Union[bool, str] = True
        The next stage for the task when submitted in current stage.
        If True, the task will go to ground truth.
        If False, the task will be archived.

    config: Config = Config()
        Stage config.
    """

    @dataclass
    class Config(Stage.Config):
        """Model Stage Config.

        Parameters
        --------------
        name: str
            Model name.

        url: Optional[str]
            URL for self-hosted model.

        taxonomy_objects: Optional[Dict[str, int]]
            Mapping of model classes to project's taxonomy objects.
        """

        name: str
        url: Optional[str] = None
        taxonomy_objects: Optional[List[ModelTaxonomyMap]] = None

        @classmethod
        def from_entity(cls, entity: Optional[Dict] = None) -> "ModelStage.Config":
            """Get object from entity."""
            if not entity:
                raise ValueError("Model name is required")
            return cls(
                name=entity["name"],
                url=entity.get("url"),
                taxonomy_objects=entity.get("taxonomyObjects"),
            )

        def to_entity(self) -> Dict:
            """Get entity from object."""
            entity: Dict[str, Any] = {"name": self.name}
            if self.url is not None:
                entity["url"] = self.url
            if self.taxonomy_objects is not None:
                entity["taxonomyObjects"] = self.taxonomy_objects
            return entity

    stage_name: str
    on_submit: Union[bool, str] = True
    config: Config = field(default_factory=Config.from_entity)

    @classmethod
    def from_entity(cls, entity: Dict) -> "ModelStage":
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
            "brickName": "model",
            "stageName": self.stage_name,
            "routing": {
                "nextStageName": self.get_next_stage(self.on_submit),
            },
            "stageConfig": self.config.to_entity(),
        }
