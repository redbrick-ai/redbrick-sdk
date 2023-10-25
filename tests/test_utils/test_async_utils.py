"""Tests for `redbrick.utils.async_utils`."""
import asyncio
import pytest

from redbrick.utils import async_utils


@pytest.mark.unit
@pytest.mark.asyncio
async def test_gather_with_concurrency__single_task():
    """Ensure `gather_with_concurrency` works with a single_task"""

    async def sample_task():
        await asyncio.sleep(0.1)
        return 42

    tasks = [sample_task()]
    result = await async_utils.gather_with_concurrency(2, tasks)
    assert result == [42]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_gather_with_concurrency__multiple_tasks():
    """Ensure `gather_with_concurrency` works with a multiple tasks"""

    async def sample_task(index):
        await asyncio.sleep(0.1)
        return index

    tasks = [sample_task(i) for i in range(5)]
    result = await async_utils.gather_with_concurrency(2, tasks)
    assert result == [0, 1, 2, 3, 4]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_gather_with_concurrency__progress_bar():
    """Ensure `gather_with_concurrency` works with the progress bar set"""

    async def sample_task(index):
        await asyncio.sleep(0.1)
        return index

    tasks = [sample_task(i) for i in range(5)]
    result = await async_utils.gather_with_concurrency(
        2, tasks, progress_bar_name="Testing", keep_progress_bar=True
    )
    assert result == [0, 1, 2, 3, 4]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_gather_with_concurrency__return_exceptions():
    """Ensure `gather_with_concurrency` return (and not raise) exceptions when the flag is set"""

    async def sample_task(index):
        if index == 2:
            raise ValueError("Sample Error")
        await asyncio.sleep(0.1)
        return index

    tasks = [sample_task(i) for i in range(5)]
    result = await async_utils.gather_with_concurrency(2, tasks, return_exceptions=True)
    assert isinstance(result[2], Exception)


@pytest.mark.unit
@pytest.mark.slow
@pytest.mark.asyncio
async def test_gather_with_concurrency__large_concurrency():
    """Ensure `gather_with_concurrency` works with a large concurrency value"""

    async def sample_task(index):
        await asyncio.sleep(0.1)
        return index

    tasks = [sample_task(i) for i in range(1_000)]
    result = await async_utils.gather_with_concurrency(100, tasks)
    assert result == list(range(1_000))


@pytest.mark.unit
@pytest.mark.asyncio
async def test_gather_with_concurrency__no_tasks():
    """Ensure `gather_with_concurrency` returns an empty result list when there are no tasks"""
    tasks = []
    result = await async_utils.gather_with_concurrency(2, tasks)
    assert result == []
