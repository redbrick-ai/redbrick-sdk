"""Stage base object."""

from abc import abstractmethod
from dataclasses import dataclass
import re
from typing import Dict, Optional, Union

from redbrick.types.taxonomy import Taxonomy


@dataclass
class Stage:
    """Base stage."""

    @dataclass
    class Config:
        """Stage config."""

        @classmethod
        @abstractmethod
        def from_entity(
            cls, entity: Optional[Dict] = None, taxonomy: Optional[Taxonomy] = None
        ) -> "Stage.Config":
            """Get object from entity"""

        @abstractmethod
        def to_entity(self, taxonomy: Optional[Taxonomy] = None) -> Dict:
            """Get entity from object."""

    stage_name: str
    config: Config

    def __post_init__(self) -> None:
        """Validate props."""
        assert re.fullmatch(r"\w{4,20}", self.stage_name, re.IGNORECASE)

    @classmethod
    @abstractmethod
    def from_entity(cls, entity: Dict, taxonomy: Optional[Taxonomy] = None) -> "Stage":
        """Get object from entity"""

    @abstractmethod
    def to_entity(self, taxonomy: Optional[Taxonomy] = None) -> Dict:
        """Get entity from object."""

    def get_next_stage(self, done: Union[bool, str]) -> str:
        """Get next stage."""
        return done if isinstance(done, str) else ("Output" if done else "ARCHIVED")
