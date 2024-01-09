"""Stage base object."""


from abc import abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class Stage:
    """Base stage."""

    @dataclass
    class Config:
        """Stage config."""

        @classmethod
        @abstractmethod
        def from_entity(cls, entity: Optional[Dict] = None) -> "Stage.Config":
            """Get object from entity"""

        @abstractmethod
        def to_entity(self) -> Dict:
            """Get entity from object."""

    stage_name: str
    config: Config

    @classmethod
    @abstractmethod
    def from_entity(cls, entity: Dict) -> "Stage":
        """Get object from entity"""

    @abstractmethod
    def to_entity(self) -> Dict:
        """Get entity from object."""
