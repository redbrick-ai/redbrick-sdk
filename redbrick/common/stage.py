"""Stage base object."""


from abc import abstractmethod
from dataclasses import dataclass
from typing import Dict


@dataclass
class Stage:
    """Base stage."""

    class Config:
        """Stage config."""

        @classmethod
        def config_factory(cls) -> "Stage.Config":
            """Get an instance of class."""
            return cls()

        @classmethod
        def from_entity(cls, entity: Dict) -> "Stage.Config":
            """Get object from entity"""
            return cls()

        @abstractmethod
        def to_entity(self) -> Dict:
            """Get entity from object."""

    stage_name: str
    config: Config

    @classmethod
    def from_entity(cls, entity: Dict) -> "Stage":
        """Get object from entity"""
        return cls(stage_name=entity["stageName"], config=cls.Config.config_factory())

    @abstractmethod
    def to_entity(self) -> Dict:
        """Get entity from object."""
