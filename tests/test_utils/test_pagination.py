"""Tests for `redbrick.utils.pagination`."""
from typing import Optional

import pytest

from redbrick.utils import pagination


@pytest.mark.unit
def mock_data_retrieval(
    concurrency: int, cursor: Optional[str]
):  # pylint: disable=unused-argument
    """Mock function to simulate the behavior of the actual data retrieval function"""
    _data = [{"id": i} for i in range(5)]
    return _data, cursor


@pytest.mark.unit
def test_pagination_iterator():
    """Test cases for the pagination.PaginationIterator class"""
    iterator = pagination.PaginationIterator(mock_data_retrieval)
    assert isinstance(iterator, pagination.PaginationIterator)
    assert iterator.cursor is None
    assert iterator.datapoints_batch is None
    assert iterator.datapoints_batch_index is None
    assert callable(iterator.func)
    assert iterator.concurrency == 10
    assert iterator.limit is None
    assert iterator.total == 0


@pytest.mark.unit
def test_pagination_iterator_iteration():
    """Check iteration"""
    iterator = pagination.PaginationIterator(mock_data_retrieval)
    assert len(iterator) == 0
    item = next(iterator)
    assert item == {"id": 0}
    assert len(iterator) == 5


@pytest.mark.unit
def test_pagination_iterator_limit():
    """Check iterator with limit"""
    iterator = pagination.PaginationIterator(mock_data_retrieval, limit=2)
    assert len(iterator) == 0
    items = list(iterator)
    assert len(items) == 2
    assert len(iterator) == 2

    assert items[0] == {"id": 0}
    assert items[1] == {"id": 1}


@pytest.mark.unit
def test_pagination_iterator_empty_data():
    """Check iterator with empty data"""

    def mock_empty_data_retrieval(
        concurrency, cursor
    ):  # pylint: disable=unused-argument
        return [], None

    iterator = pagination.PaginationIterator(mock_empty_data_retrieval)
    items = list(iterator)
    assert len(items) == 0


@pytest.mark.unit
def test_pagination_iterator_custom_concurrency():
    """Check that `concurrency` gets to the passed function"""

    def mock_empty_data_retrieval(
        concurrency, cursor
    ):  # pylint: disable=unused-argument
        return [concurrency for _ in range(5)], None

    iterator = pagination.PaginationIterator(mock_empty_data_retrieval, concurrency=4)
    item = next(iterator)
    assert item == 4


@pytest.mark.unit
def test_pagination_iterator_task_exception():
    """Check iterator propagates exceptions from passed function"""

    def mock_data_retrieval_exception(
        concurrency, cursor
    ):  # pylint: disable=unused-argument
        if cursor is None:
            return [{"id": 1}, {"id": 2}], "cursor"
        raise Exception("An error occurred")

    iterator = pagination.PaginationIterator(mock_data_retrieval_exception)
    with pytest.raises(Exception):
        list(iterator)


@pytest.mark.unit
def test_pagination_iterator_exception_data_exhausted():
    """Assert a StopIteration is raised on iteration after data exhaustion"""
    iterator = pagination.PaginationIterator(mock_data_retrieval)
    list(iterator)
    with pytest.raises(StopIteration):
        next(iterator)


@pytest.mark.unit
def test_pagination_iterator_multiple_iterations():
    """Check multiple iterations"""
    iterator = pagination.PaginationIterator(mock_data_retrieval)
    assert len(iterator) == 0

    items = next(iterator)
    assert len(items) == 1
    assert len(iterator) == 5

    items = next(iterator)
    assert len(items) == 1
    assert len(iterator) == 5
