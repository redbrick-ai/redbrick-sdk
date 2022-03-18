"""A utility iterator to handle default RedBrick pagination behavior."""

from typing import Any, Dict, List, Optional, Callable, Tuple


class PaginationIterator:
    """Construct Labelset Iterator."""

    def __init__(self, func: Callable[[Optional[str]], Tuple[Any, ...]]) -> None:
        """Construct LabelsetIterator."""
        self.cursor: Optional[str] = None
        self.datapoints_batch: Optional[List[Dict]] = None
        self.datapoints_batch_index: Optional[int] = None

        self.func = func

        self.total = 0

    def __iter__(self) -> Any:
        """Get iterator."""
        return self

    def __len__(self) -> int:
        """Get length of iteration."""
        return self.total

    def __next__(self) -> Dict:
        """Get next batch of labels / datapoint."""
        # If cursor is None and current datapoints_batch has been processed
        if (
            self.datapoints_batch_index is not None
            and self.cursor is None
            and self.datapoints_batch
            and len(self.datapoints_batch) == self.datapoints_batch_index
        ):
            raise StopIteration

        # If current datapoints_batch is None or we have finished
        # processing current datapoints_batch
        if (
            self.datapoints_batch is None
            or len(self.datapoints_batch) == self.datapoints_batch_index
        ):
            # When no data is returned in the current iteration,
            # but there is still more data, go for the next iteration
            while True:
                self.datapoints_batch, self.cursor, *_ = self.func(self.cursor)
                if not self.datapoints_batch and self.cursor:
                    continue
                self.datapoints_batch_index = 0
                self.total += len(self.datapoints_batch)  # type: ignore
                break

        # Current entry to return
        if self.datapoints_batch and self.datapoints_batch_index is not None:
            entry = self.datapoints_batch[self.datapoints_batch_index]
            self.datapoints_batch_index += 1

            return entry

        raise StopIteration
