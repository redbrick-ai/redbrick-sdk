"""Async utils."""

import asyncio
from typing import Generator, Sequence, Awaitable, List, TypeVar, Optional, Iterable
import tqdm.asyncio  # type: ignore

ReturnType = TypeVar("ReturnType")


async def gather_with_concurrency(
    max_concurrency: int,
    tasks: Iterable[Awaitable[ReturnType]],
    progress_bar_name: Optional[str] = None,
) -> List[ReturnType]:
    """Utilizes a Semaphore to limit concurrency to n."""
    semaphore = asyncio.Semaphore(max_concurrency)

    async def sem_task(task: Awaitable[ReturnType]) -> ReturnType:
        async with semaphore:
            return await task

    coros = [sem_task(task) for task in tasks]

    if progress_bar_name:
        result = []
        print(progress_bar_name)
        for f in tqdm.asyncio.tqdm.as_completed(coros):
            temp = await f
            result.append(temp)
        return result

    return await asyncio.gather(*coros)
