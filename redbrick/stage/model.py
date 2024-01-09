"""Model stage."""


from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from redbrick.common.stage import Stage


@dataclass
class ModelStage(Stage):
    """Model Stage.

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

        name: Optional[str] = None
        url: Optional[str] = None
        taxonomy_objects: Optional[Dict[str, int]] = None

        @classmethod
        def config_factory(cls) -> "ModelStage.Config":
            """Get an instance of class."""
            return cls()

        @classmethod
        def from_entity(cls, entity: Dict) -> "ModelStage.Config":
            """Get object from entity."""
            return cls(
                name=entity["name"],
                url=entity.get("url"),
                taxonomyObjects=entity.get("taxonomy_objects"),
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
    on_submit: Optional[str] = None
    config: Config = field(default_factory=Config.config_factory)

    @classmethod
    def from_entity(cls, entity: Dict) -> "ModelStage":
        """Get object from entity"""
        return cls(
            stage_name=entity["stageName"],
            on_submit=entity["routing"]["nextStageName"],
            config=cls.Config.from_entity(entity.get("stageConfig") or {}),
        )

    def to_entity(self) -> Dict:
        """Get entity from object."""
        return {
            "brickName": "model",
            "stageName": self.stage_name,
            "routing": {
                "nextStageName": self.on_submit or "Output",
            },
            "stageConfig": self.config.to_entity(),
        }
