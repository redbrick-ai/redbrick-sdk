"""A utility iterator to handle default RedBrick pagination behavior."""

from typing import Any, Dict, Iterable, List, Optional, Callable, Tuple


class PaginationIterator:
    """Construct Labelset Iterator."""

    def __init__(
        self, func: Callable[[Optional[str]], Tuple[List[Dict], Optional[str]]]
    ) -> None:
        """Construct LabelsetIterator."""
        self.cursor: Optional[str] = None
        self.datapointsBatch: Optional[List[Dict]] = None
        self.datapointsBatchIndex: Optional[int] = None

        self.func = func

        self.total = 0

    def __iter__(self) -> Any:
        return self

    def __len__(self) -> int:
        return self.total

    def __next__(self) -> Dict:
        """Get next batch of labels / datapoint."""
        # If cursor is None and current datapointsBatch has been processed
        if (
            self.datapointsBatchIndex is not None
            and self.cursor is None
            and self.datapointsBatch
            and len(self.datapointsBatch) == self.datapointsBatchIndex
        ):
            raise StopIteration

        # If current datapointsBatch is None or we have finished processing current datapointsBatch
        if (
            self.datapointsBatch is None
            or len(self.datapointsBatch) == self.datapointsBatchIndex
        ):

            self.datapointsBatch, self.cursor = self.func(self.cursor)
            self.datapointsBatchIndex = 0

            self.total += len(self.datapointsBatch)

        # Current entry to return
        if self.datapointsBatch and self.datapointsBatchIndex is not None:
            entry = self.datapointsBatch[self.datapointsBatchIndex]
            self.datapointsBatchIndex += 1

            return entry

        raise StopIteration
