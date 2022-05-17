"""Async utils."""
import asyncio
from typing import Awaitable, Coroutine, List, Tuple, TypeVar, Optional, Iterable
import tqdm.asyncio

from redbrick.common.constants import MAX_CONCURRENCY

ReturnType = TypeVar("ReturnType")


async def gather_with_concurrency(
    max_concurrency: int,
    tasks: Iterable[Awaitable[ReturnType]],
    progress_bar_name: Optional[str] = None,
    keep_progress_bar: bool = True,
) -> List[ReturnType]:
    """Utilizes a Semaphore to limit concurrency to n."""
    if not tasks:
        return []

    max_concurrency = min(max_concurrency, MAX_CONCURRENCY)
    semaphore = asyncio.Semaphore(max_concurrency)

    async def sem_task(task: Awaitable[ReturnType]) -> ReturnType:
        async with semaphore:
            return await task

    coros = [sem_task(task) for task in tasks]
    if not progress_bar_name:
        return await asyncio.gather(*coros)

    async def ordered_coroutine(idx: int, task: Coroutine) -> Tuple[int, ReturnType]:
        """Return the index and result of a task."""
        return idx, await task

    ordered_coros = [ordered_coroutine(idx, task) for idx, task in enumerate(coros)]
    result: List[Tuple[int, ReturnType]] = []

    for coro in tqdm.asyncio.tqdm.as_completed(
        ordered_coros, desc=progress_bar_name, leave=keep_progress_bar
    ):
        temp = await coro
        result.append(temp)

    return [res[1] for res in sorted(result, key=lambda x: x[0])]
