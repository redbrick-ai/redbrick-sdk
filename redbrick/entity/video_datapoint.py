from typing import List, Optional, Union
from .taxonomy import TaxonomyEntry


class VideoDatapoint:
    def __init__(
        self,
        org_id: str,
        label_set_name: str,
        items: list,
        items_not_signed: list,
        task_type: str,
        labels: dict,
        name: str,
        taxonomy: Optional[TaxonomyEntry] = None,
    ) -> None:
        """Construct a video datapoint."""
        self.org_id = org_id
        self.label_set_name = label_set_name
        self.items = items
        self.items_not_signed = items_not_signed
        self.task_type = task_type
        self.labels = labels
        self.name = name
        self.taxonomy = taxonomy
