"""Stage base object."""

from abc import abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional, Union


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

    def get_next_stage(self, done: Union[bool, str]) -> str:
        """Get next stage."""
        return done if isinstance(done, str) else ("Output" if done else "ARCHIVED")
