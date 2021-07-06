"""Taxonomy."""
from dataclasses import dataclass


@dataclass
class TaxonomyEntry:
    """A single entry to the taxonomy object."""

    class_name: str
    class_id: str
