"""Async utils."""
import asyncio
from typing import Awaitable, List, TypeVar, Optional, Iterable
import tqdm.asyncio

from redbrick.common.constants import MAX_CONCURRENCY

ReturnType = TypeVar("ReturnType")


async def gather_with_concurrency(
    max_concurrency: int,
    tasks: Iterable[Awaitable[ReturnType]],
    progress_bar_name: Optional[str] = None,
    keep_progress_bar: Optional[bool] = True,
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

    if progress_bar_name:
        result = []
        for coro in tqdm.asyncio.tqdm.as_completed(
            coros, desc=progress_bar_name, leave=keep_progress_bar
        ):
            temp = await coro
            result.append(temp)
        return result

    return await asyncio.gather(*coros)
